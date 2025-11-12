import duckdb
import pandas as pd
import numpy as np
import os
import json
import yaml
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from dvclive import Live
from app.utils.log_config import logger

from app.utils.model_loader import load_model

#  CONFIGURACIÓN DE RUTAS 
BASE_DIR = "app/data"
DB_PATH = os.path.join(BASE_DIR, "DB/entrenamiento.duckdb")
METRICS_DB_PATH = os.path.join(BASE_DIR, "DB/experimento.duckdb")
MODEL_DIR = os.path.join(BASE_DIR, "artifacts/housing_models")
MODEL_RF_PATH = os.path.join(MODEL_DIR, "random_forest.joblib")
MODEL_GB_PATH = os.path.join(MODEL_DIR, "gradient_boosting.joblib")
MANIFEST_PATH = os.path.join(MODEL_DIR, "manifest.json")
METRICS_DIR = os.path.join(BASE_DIR, "metrics")
PARAMS_PATH = os.path.join(METRICS_DIR, "params.yaml")

#   FEATURE ENGINEERING Y LIMPIEZA 

def profile(df: pd.DataFrame):
    """Genera un perfil estadístico del DataFrame."""
    logger.info("Generando perfil de datos...")
    return pd.DataFrame(
        {
            "dtype": df.dtypes,
            "n_nulls": df.isnull().sum(),
            "n_unique": df.nunique(),
            "min": df.min(numeric_only=True),
            "Q1": df.quantile(0.25, numeric_only=True),
            "median": df.median(numeric_only=True),
            "mean": df.mean(numeric_only=True),
            "Q3": df.quantile(0.75, numeric_only=True),
            "max": df.max(numeric_only=True),
        }
    )

def clip_outliers(df, profile_df):
    """Recorta outliers usando el método IQR (clip, sin eliminar filas)."""
    logger.info("Recortando outliers (clip)...")
    df_clipped = df.copy()
    for col in df_clipped.select_dtypes(include=np.number).columns:
        if col in profile_df.index:
            Q1 = profile_df.loc[col, "Q1"]
            Q3 = profile_df.loc[col, "Q3"]
            IQR = Q3 - Q1
            if pd.notna(IQR) and IQR > 0:
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                df_clipped[col] = df_clipped[col].clip(lower, upper)
    return df_clipped

def clean_temporal_columns(df, date_cols, placeholder="9999-12-31"):
    """Limpia columnas de fecha, reemplaza placeholders y convierte a datetime."""
    logger.info("Limpiando columnas temporales...")
    for col in date_cols:
        if col in df.columns:
            if df[col].astype(str).str.contains(placeholder).any():
                df[col] = df[col].replace(placeholder, pd.NA)
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def create_features(df):
    """Crea nuevas features a partir de las columnas existentes."""
    logger.info("Creando nuevas features (days_active, created_age_days)...")
    df["days_active"] = (df["end_date"] - df["start_date"]).dt.days.astype(float)
    df["created_age_days"] = (pd.Timestamp.today() - df["created_on"]).dt.days.astype(float)
    return df

#  FUNCIONES DE EVALUACIÓN Y GUARDADO 

def evaluate(model, X_te, y_te, name="model"):
    """Calcula métricas de regresión (RMSE, MAE, R2)."""
    y_pred = model.predict(X_te)
    rmse = mean_squared_error(y_te, y_pred) ** 0.5
    mae = mean_absolute_error(y_te, y_pred)
    r2 = r2_score(y_te, y_pred)
    logger.info(f"--- {name} --- RMSE: {rmse:.2f}, MAE: {mae:.2f}, R2: {r2:.4f}")
    return {"rmse": float(rmse), "mae": float(mae), "r2": float(r2)}

def save_metrics_to_duckdb(params, metrics_rf, metrics_gb):
    """Guarda los parámetros y métricas de la ejecución en la DB de experimentos."""
    logger.info(f"Guardando métricas en DuckDB: {METRICS_DB_PATH}")
    os.makedirs(os.path.dirname(METRICS_DB_PATH), exist_ok=True)
    con = duckdb.connect(METRICS_DB_PATH)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS metricas (
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        experimento TEXT,
        modelo TEXT,
        rmse DOUBLE,
        mae DOUBLE,
        r2 DOUBLE,
        rf_n_estimators INTEGER,
        rf_min_samples_split INTEGER,
        gb_n_estimators INTEGER,
        gb_learning_rate DOUBLE,
        gb_max_depth INTEGER,
        gb_subsample DOUBLE,
        test_size DOUBLE
    )""")

    exp_name = "exp_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extrae parámetros 
    rf_n_estimators = params.get("rf_n_estimators")
    rf_min_samples_split = params.get("rf_min_samples_split")
    gb_n_estimators = params.get("gb_n_estimators")
    gb_learning_rate = params.get("gb_learning_rate")
    gb_max_depth = params.get("gb_max_depth")
    gb_subsample = params.get("gb_subsample")
    test_size = params.get("split_test_size", 0.2)

    # Insertar métricas  de RandomForest en tabla
    con.execute("""
    INSERT INTO metricas VALUES (
        CURRENT_TIMESTAMP, ?, 'RandomForest', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )""", [
        exp_name,
        metrics_rf["rmse"], metrics_rf["mae"], metrics_rf["r2"],
        rf_n_estimators, rf_min_samples_split,
        None, None, None, None,
        test_size,
    ])

    # Insertar métricas de GradientBoosting
    con.execute("""
    INSERT INTO metricas VALUES (
        CURRENT_TIMESTAMP, ?, 'GradientBoosting', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )""", [
        exp_name,
        metrics_gb["rmse"], metrics_gb["mae"], metrics_gb["r2"],
        None, None,
        gb_n_estimators, gb_learning_rate, gb_max_depth, gb_subsample,
        test_size,
    ])

    con.close()
    logger.info(f"Métricas guardadas exitosamente para el experimento: {exp_name}")

#  PIPELINE  DE ENTRENAMIENTO 

def run_training_pipeline():
    """Función principal que ejecuta todo el pipeline de entrenamiento."""
    logger.info("--- Iniciando Pipeline de Entrenamiento ---")
    
    try:
        #  Cargar datos desde DuckDB (generados por la ingesta)
        logger.info(f"Conectando a DuckDB en {DB_PATH} para cargar datos...")
        con = duckdb.connect(DB_PATH)
        # Filtramos solo CABA (l2 = 'Capital Federal') y Venta
        df_raw = con.execute("""
            SELECT * FROM datos_raw 
            WHERE l2 = 'Capital Federal' AND operation_type = 'Venta'
        """).df()
        con.close()
        
        if df_raw.empty:
            logger.error("No se encontraron datos en 'datos_raw'. Exit entrenamiento.")
            return {"status": "error", "message": "No hay datos para entrenar."}
            
        logger.info(f"Datos cargados: {df_raw.shape[0]} filas.")

        #  Limpieza de datos
        df = df_raw.drop(columns=["l1", "l2", "l4", "l5", "l6", "ad_type", "title", "description", "id"], errors='ignore')
        df = clean_temporal_columns(df, ["start_date", "end_date", "created_on"])

        #  Profiling y Clipping de Outliers
        profile_df = profile(df)
        df = clip_outliers(df, profile_df)

        #  Feature Engineering
        df = create_features(df)
        
        #  Guardar datos limpios en DuckDB 
        logger.info(f"Guardando datos limpios en la tabla 'datos_clean' de {DB_PATH}...")
        try:
            con = duckdb.connect(DB_PATH)
            con.register("df_clean_temp", df)
            con.execute("""
                CREATE OR REPLACE TABLE datos_clean AS 
                SELECT * FROM df_clean_temp
            """)
            con.close()
            logger.info("Tabla 'datos_clean' guardada")
        except Exception as e:
            logger.error(f"No se pudo guardar la tabla 'datos_clean': {e}")
       

        # Definición de Features y Target
        numeric_feats = [
            "lon", "lat", "rooms", "bedrooms", "bathrooms",
            "surface_total", "surface_covered", "days_active", "created_age_days",
        ]
        categorical_feats = [
            "l3", "currency", "price_period", "property_type", "operation_type",
        ]
        
        # Eliminar filas donde el target (price) es nulo
        df = df.dropna(subset=["price"])
        X = df[numeric_feats + categorical_feats].copy()
        y = df["price"].values
        logger.info(f"Datos listos para entrenamiento: {X.shape[0]} filas.")

        #  División Train/Test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        #   Pipelines de Preprocesamiento
        num_transform_rf = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("robust_scaler", RobustScaler()),
        ])
        num_transform_gb = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        cat_transform = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        preproc_rf = ColumnTransformer([
            ("num", num_transform_rf, numeric_feats),
            ("cat", cat_transform, categorical_feats),
        ])
        preproc_gb = ColumnTransformer([
            ("num", num_transform_gb, numeric_feats),
            ("cat", cat_transform, categorical_feats),
        ])

        #  Parámetros y Modelos
        params = {
            "split_test_size": 0.2,
            "rf_n_estimators": 100,
            "rf_min_samples_split": 4,
            "rf_scaler": "RobustScaler",
            "gb_n_estimators": 200,
            "gb_learning_rate": 0.05,
            "gb_max_depth": 3,
            "gb_subsample": 0.8,
            "numeric_features": numeric_feats,
            "categorical_features": categorical_feats,
        }
        
        rf_regressor = RandomForestRegressor(
            n_estimators=params["rf_n_estimators"],
            min_samples_split=params["rf_min_samples_split"],
            n_jobs=-1,
            random_state=42,
        )
        
        # Transformamos el target (log-transform) para RF
        model_rf = Pipeline([
            ("preproc", preproc_rf),
            ("est", TransformedTargetRegressor(
                regressor=rf_regressor, func=np.log1p, inverse_func=np.expm1
            )),
        ])

        model_gb = Pipeline([
            ("preprocessor", preproc_gb),
            ("model", GradientBoostingRegressor(
                n_estimators=params["gb_n_estimators"],
                learning_rate=params["gb_learning_rate"],
                max_depth=params["gb_max_depth"],
                subsample=params["gb_subsample"],
                random_state=42,
            )),
        ])
        
        #  Entrenamiento y Logging con DVCLive
        os.makedirs(METRICS_DIR, exist_ok=True)
        
        with Live(METRICS_DIR, save_dvc_exp=False, resume=True) as live:
            live.log_params(params)
            
            logger.info("Entrenando modelo A RandomForest...")
            model_rf.fit(X_train, y_train)
            logger.info("Entrenamiento de RandomForest completo.")

            logger.info("Entrenando modelo B GradientBoosting...")
            model_gb.fit(X_train, y_train)
            logger.info("Entrenamiento de GradientBoosting completo.")
            
            #  Evaluación
            logger.info("Evaluando modelos...")
            metrics_rf = evaluate(model_rf, X_test, y_test, name="RandomForest")
            metrics_gb = evaluate(model_gb, X_test, y_test, name="GradientBoosting")

            # Loggear métricas
            live.log_metric("rf_rmse", metrics_rf["rmse"])
            live.log_metric("rf_mae", metrics_rf["mae"])
            live.log_metric("rf_r2", metrics_rf["r2"])
            live.log_metric("gb_rmse", metrics_gb["rmse"])
            live.log_metric("gb_mae", metrics_gb["mae"])
            live.log_metric("gb_r2", metrics_gb["r2"])
            
            #  Guardar modelos .joblib
            os.makedirs(MODEL_DIR, exist_ok=True)
            logger.info(f"Guardando RandomForest en: {MODEL_RF_PATH}")
            joblib.dump(model_rf, MODEL_RF_PATH)
            logger.info(f"Guardando GradientBoosting en: {MODEL_GB_PATH}")
            joblib.dump(model_gb, MODEL_GB_PATH)

            #  Guardar Manifiesto
            manifest = {
                "models": [
                    {"name": "RandomForest", "path": MODEL_RF_PATH, "metrics": metrics_rf},
                    {"name": "GradientBoosting", "path": MODEL_GB_PATH, "metrics": metrics_gb},
                ]
            }
            with open(MANIFEST_PATH, "w") as f:
                json.dump(manifest, f, indent=2)
            
            #  Guardar métricas en DuckDB
            save_metrics_to_duckdb(params, metrics_rf, metrics_gb)
        
        #  Recargar el modelo en la API 
        logger.info("Entrenamiento finalizado. Recargando el modelo en la API...")
        
        load_model(force_reload=True) 
        logger.info("Modelo recargado en la caché ")
        
        logger.info("--- Pipeline de Entrenamiento Finalizado ---")
        return {"status": "ok", "message": "Entrenamiento completo y modelo recargado.", "metrics_rf": metrics_rf, "metrics_gb": metrics_gb}

    except Exception as e:
        logger.error(f"ERROR en el pipeline de entrenamiento: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Para ejecutar el entrenamiento manualmente (opcional)
    # python -m app.processing.trainer
    logger.info("Ejecutando trainer.py como script independiente...")
    run_training_pipeline()