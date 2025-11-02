import duckdb
import pandas as pd

##TODO: Falta bajar el dataset directamente de Kaggle
# import kagglehub
# from kagglehub import KaggleDatasetAdapter

# # Load the dataset from KaggleHub
# df = kagglehub.load_dataset(
#     KaggleDatasetAdapter.PANDAS,
#     "alejandroczernikier/properati-argentina-dataset",
#     file_path="/data/raw"
# )

df = pd.read_csv("data/RAW/entrenamiento.csv")

con = duckdb.connect("entrenamiento.duckdb")
con.register("entrenamiento_df", df)
con.execute("COPY entrenamiento_df TO 'data/parquet/entrenamiento.parquet' (FORMAT 'parquet')")

#guardarlo en duckdb

con = duckdb.connect("data/DB/entrenamiento.duckdb")

# Crear tabla desde el archivo Parquet
con.execute("""
    CREATE TABLE entrenamiento AS
    SELECT * FROM 'data/parquet/entrenamiento.parquet'
""")

