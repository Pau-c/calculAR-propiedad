## Propósito

Este archivo orienta a agentes AI (Copilot/assistentes) para ser productivos rápidamente en este repositorio Python + Jupyter. Describe la arquitectura mínima, puntos clave de datos, comandos de arranque y convenciones concretas detectadas en el código.

## Visión general rápida

- Tipo de proyecto: Python + Jupyter (no es una aplicación web completa). Hay notebooks para ETL/DB y un script `main.py` como punto de entrada mínimo.
- Datos: `data/parquet/RAW/entrenamiento.csv` (raw) y `data/DB/entrenamiento.duckdb` (repositorio DuckDB usado para persistencia/consultas).
- Dependencias principales (ver `pyproject.toml`): duckdb, pandas, scikit-learn, pydantic, fastapi/uvicorn (presentes en deps pero no hay servidor expuesto por defecto), joblib, loguru.

## Archivos y patrones importantes (referencias concretas)

- `main.py`: script de arranque. Actualmente solo imprime un saludo. No asume un servidor FastAPI por defecto.
- `load_save_db.ipynb`: notebook para trabajar con DuckDB y los datasets; aquí están los pasos de carga/guardado de `entrenamiento.duckdb`.
- `pyproject.toml`: lista de dependencias y configuración de `commitizen` (convención de commits del proyecto). Revisa ahí la lista de paquetes y la versión requerida de Python.

## Cómo ponerse en marcha (comandos concretos)

1. Usar la versión de Python requerida: pyproject especifica "requires-python = \">=3.13,<3.14\"" — mantener ese entorno por compatibilidad con la versión de `duckdb` usada.
2. Crear un entorno virtual y actualizar pip:

   python -m venv .venv
   .venv\Scripts\Activate.ps1  # PowerShell
   python -m pip install -U pip

3. Instalar dependencias (lista tomada de `pyproject.toml`):

   python -m pip install duckdb fastapi ipykernel joblib jupyter kagglehub[pandas-datasets] loguru pandas pydantic python-dotenv scikit-learn uvicorn

4. Para trabajar con los datos: abrir `load_save_db.ipynb` en Jupyter (o usar `ipython`/scripts) y seguir las celdas — el notebook contiene la lógica de carga/guardado hacia `data/DB/entrenamiento.duckdb`.

5. Ejecutar el script principal (actualmente es un stub):

   python main.py

Nota: aunque `fastapi` y `uvicorn` están en dependencias, no existe un `app` expuesto en `main.py` — si se añade un servicio FastAPI, usar `uvicorn main:app --reload` si la variable `app` está definida.

## Convenciones del repositorio detectadas

- Control de commits: el proyecto usa `commitizen` (configuración en `pyproject.toml`) con tipos: feat, fix, chore, docs, refactor, perf, test. Generar mensajes que cumplan el esquema.
- Almacenar artefactos derivados en `data/DB/` (DuckDB) y dejar los datos raw en `data/parquet/RAW/`.
- Evitar cambiar la versión de Python sin antes validar `duckdb` localmente (hay un comentario en `pyproject.toml` que indica cuidados con versiones >3.13).

## Qué puede pedir un agente AI (ejemplos concretos)

- "Abrir y resumir `load_save_db.ipynb` y extraer los pasos de ETL" — abrir el notebook y extraer las celdas relevantes (entrada CSV → transformaciones → persistencia DuckDB).
- "Agregar una pequeña API para exponer predicciones" — crear `app = FastAPI()` en un nuevo `api.py` o en `main.py`, agregar endpoint `/predict` que cargue el modelo desde `joblib`/ruta definida y devuelva JSON; usar `uvicorn` para desarrollo.
- "Actualizar dependencias" — editar `pyproject.toml` y probar en un entorno virtual; ejecutar el notebook de carga para validar que DuckDB funciona con la nueva versión.

## Límites y supuestos

- No hay tests automatizados visibles; no asumir workflow de CI existente.
- No hay Dockerfile ni configuración de packaging completa en `pyproject.toml` (falta sección `[build-system]`), así que la instalación editable (`pip install -e .`) puede no funcionar sin añadirla.

## Preguntas útiles para el mantenedor

- ¿Desea una API REST ya integrada en el repo o prefieres mantener la lógica en notebooks por ahora?
- ¿Cuál es el flujo esperado para regenerar `data/DB/entrenamiento.duckdb` (notebook manual o script automatizado)?

---
Si quieres que fusione/ajuste texto existente (si tienes un `.github/copilot-instructions.md` previo o notas en otro fichero), pásamelo y lo integro. ¿Hay alguna convención adicional que deba incluir (CI, secrets, rutas absolutas)?
