# Presentación
<img width="1024" height="690" alt="TP integrador" src="https://github.com/user-attachments/assets/18569c46-2485-44b9-9552-a55de1004d0b" />





---
## Materia: Programación Avanzada en Ciencia de Datos
## Integrantes

- Ariel Omar Leche
- Diego Ariel Gutierrez 
- José Alberto Rubio
- Maria Paula Cobas
- Mauro Ruben De Natale


> [!TIP]
>[Repo en Github](https://github.com/Pau-c/calculAR-propiedad)


<!-- PROJECT SHIELDS -->
[![datadogBadge][datadog-shield]][datadog-url]
[![dockerBadge][docker-shield]][docker-url]
[![duckDBBadge][duckDB-shield]][duckDB-url]
[![fastapiBadge][fastapi-shield]][fastapi-url]
[![jupyterBadge][jupyter-shield]][jupyter-url]
[![joblibBadge][joblib-shield]][joblib-url]
[![loguruBadge][loguru-shield]][loguru-url]
[![pandasBadge][pandas-shield]][pandas-url]
[![pydanticBadge][pydantic-shield]][pydantic-url]
[![pythonBadge][python-shield]][python-url]
[![scikitlearnBadge][scikitlearn-shield]][scikitlearn-url]
[![uvBadge][uv-shield]][uv-url]
[![uvicornBadge][uvicorn-shield]][uvicorn-url]
<!-- PROJECT SHIELDS -->

## Instrucciones 

### 🛠️ Requisitos e Instalación

#### - Instalar `Docker` desktop
#### - Instalar `duckDBCLI` 
```
winget install DuckDB.cli
```

#### - Instalar `uv` en la pc Windows si es necesario (en terminal de Windows):
<details>

   Abrir un prompt CMD en win  o terminal ID, ver el prompt con PS:>    y ejecutar:

```
 powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### - Instalar uv  (Linux)

### Instalar curl si no lo tenes
```
sudo apt update
```
```
sudo apt install curl
```
### Descargar e instalar uv
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
### Recargar el profile 
```
source ~/.bashrc  # Para Bash
```
source ~/.zshrc   # Para Zsh
</details>

#### - Clonar repo:
```
git clone https://github.com/Pau-c/calculAR-propiedad.git
```

#### - Abrir el proyecto en IDE
#### - Bajar dataset de [Kaggle](https://www.kaggle.com/datasets/alejandroczernikier/properati-argentina-dataset) 
#### - Poner el `.CSV` en la carpeta RAW: `app/data/artifacts/RAW`
#### - Correr la notebook `load_save_db.ipynb`



*****************************************************************************************************************
**PASOS PARA USAR CON DOCKER**
****************************************************************************************************************
<details>

#### - Tener el servicio de Docker corriendo
#### -  Ir a carpeta de proyecto en terminal:
```
docker compose up --build
```
### - Para volver a correr el proyecto dentro del contenedor si no hubo cambios:
```
docker compose up 
```

### - Abrir proyecto en un browser:
```
http://127.0.0.1:8000/docs
```
</details>

***************************************************************************************************************
**NOTA SOBRE COMMITS:**
****************************************************************************************************************

#### - El proyecto usa commitizens para estandarizar los mensajes de commits, en vez de 'git commit' usar comando `cz commit` y seguir las instrucciones en la terminal

***************************************************************************************************************
**PASOS PARA USAR en IDE SIN DOCKER con UV y COMENZAR DESARROLLO**
****************************************************************************************************************
<details>

### - Crear entorno virtual:
Si todavía no se instaló uv en el sistema como en el primer paso, en terminal: `pip install uv` y luego  ejecutar:

```
uv venv
```

### - Sincronizar entorno virtual al instalar el proyecto y luego de cada cambio en el .toml
```
uv sync
```

### -Elegir kernel
>Para que el código del notebook funcione,  indicarle a VS Code que utilice el Python >que está dentro del nuevo entorno. Esto se hace dentro de la interfaz del notebook:

> [!IMPORTANT]
> Abrir el archivo `.ipynb` en VS Code.
> 1. Hacer clic en el selector del kernel (la esquina superior derecha).
> 2. Seleccionar otro kernel.
> 3. Elegir el kernel que tenga el nombre del proyecto.


#### Asegurarse estar en el etorno correcto y activado: De ser necesario correr en terminal: `.venv\Scripts\activate`
#### En linux: `source .venv/bin/activate`


### - Correr en `load_save_db.ipynb` para generar los modelos a traves del notebook

### - Ejecutar el proyecto localmente en terminal con:
```
uvicorn main:app --reload --port 8000
```

### - Abrir proyecto en browser para ver los endpoints:
```
http://127.0.0.1:8000/docs
```
</details>

<!-- PROJECT SHIELDS VARIABLES-->
[datadog-shield]:https://img.shields.io/badge/Observability-Datadog-black?style=flat&labelColor=%23808080k&color=81493b&logo=datadog&logoColor=white
[datadog-url]: https://www.datadoghq.com/
[deepnote-shield]:https://img.shields.io/badge/Live-Deepnote-black?style=flat&labelColor=%23808080k&color=d65e40&logo=deepnote&logoColor=white
[deepnote-url]: https://deepnote.com/
[docker-shield]:https://img.shields.io/badge/Container-Docker-black?style=flat&labelColor=%23808080k&color=f7b387&logo=docker&logoColor=white
[docker-url]: https://www.docker.com
[dotenv-shield]:https://img.shields.io/badge/Env-Dotenv-black?style=flat&labelColor=%23808080k&color=f3edb9&logo=dotenv&logoColor=white
[dotenv-url]:https://pypi.org/project/python-dotenv/
[duckDB-shield]:https://img.shields.io/badge/BD-duckDB-black?style=flat&labelColor=%23808080k&color=f7b387&logo=duckDB&logoColor=white
[duckDB-url]: https://duckdb.org/
[fastapi-shield]:https://img.shields.io/badge/Framework-Fastapi-black?style=flat&labelColor=%23808080k&color=b0c69a&logo=fastapi&logoColor=white
[fastapi-url]: https://fastapi.tiangolo.com/
[joblib-shield]:https://img.shields.io/badge/Serializer-Joblib-black?style=flat&labelColor=%23808080k&color=70b29c&logo=joblib&logoColor=white
[joblib-url]:https://joblib.readthedocs.io/en/stable/
[jupyter-shield]:https://img.shields.io/badge/Notebook-Jupyter-black?style=flat&labelColor=%23808080k&color=2a9ca0&logo=Jupyter&logoColor=white
[jupyter-url]: https://jupyter.org/
[loguru-shield]:https://img.shields.io/badge/Logger-Loguru-black?style=flat&labelColor=%23808080k&color=2a6478&logo=loguru
[loguru-url]:https://pandas.pydata.org/
[pandas-shield]:https://img.shields.io/badge/Data_analysis-Pandas-black?style=flat&labelColor=%23808080k&color=4c4e77&logo=pandas
[pandas-url]:https://pandas.pydata.org/
[plotly-shield]:https://img.shields.io/badge/Data_Viz-Plotly-black?style=flat&labelColor=%23808080k&color=133337&logo=plotly&logoColor=white
[plotly-url]: https://plotly.com/python/
[pydantic-shield]:https://img.shields.io/badge/Validation-Pydantic-black?style=flat&labelColor=%23808080k&color=81493b&logo=pydantic&logoColor=white
[pydantic-url]: https://docs.pydantic.dev/latest/
[python-shield]:https://img.shields.io/badge/Language-Python-black?style=flat&labelColor=%23808080k&color=d65e40&logo=python&logoColor=white
[python-url]: https://www.python.org/
[scikitlearn-shield]:https://img.shields.io/badge/ML-Scikitlearn-black?style=flat&labelColor=%23808080k&color=f7b387&logo=scikitlearn&logoColor=white
[scikitlearn-url]: https://scikit-learn.org/
[supabase-shield]:https://img.shields.io/badge/DB-Supabase-black?style=flat&labelColor=%23808080k&color=166866&logo=supabase&logoColor=white
[supabase-url]: https://supabase.com/
[uv-shield]:https://img.shields.io/badge/Dependencies-UV-black?style=flat&labelColor=%23808080k&color=2a0944&logo=uv&logoColor=white
[uv-url]: https://github.com/astral-sh/uv
[uvicorn-shield]:https://img.shields.io/badge/Server-Uvicorn-black?style=flat&labelColor=%23808080k&color=166866&logo=uvicorn&logoColor=white
[uvicorn-url]: https://uvicorn.dev/

---

 🚀 _Powered by Vibecoding_ 
