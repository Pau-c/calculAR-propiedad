from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from app.utils.log_config import logger
from ddtrace import tracer

# --- ERROR HANDLING ---

async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    # Maneja errores de validación de la request de FastAPI/Pydantic
    error_details = exc.errors()
    error_source = "FastAPI Request"

    logger.error(f"Error de validación ({error_source}) en {request.url}: {error_details}")
    
    span = tracer.current_span()
    if span:
        span.set_tag("validation.error_source", error_source)
        span.set_tag("validation.error_count", len(error_details))
        span.set_tag("request.url", str(request.url))
    
    # Usar jsonable_encoder para asegurar que los errores sean serializables a JSON 
    safe_content = jsonable_encoder({"detail": error_details})
    return JSONResponse(status_code=422, content=safe_content)


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    # Maneja errores de validación interna de Pydantic 
    error_details = exc.errors()
    error_source = "Pydantic Interna"

    logger.error(f"Error de validación ({error_source}) en {request.url}: {error_details}")
    
    span = tracer.current_span()
    if span:
        span.set_tag("validation.error_source", error_source)
        span.set_tag("validation.error_count", len(error_details))
        span.set_tag("request.url", str(request.url))
  
    safe_content = jsonable_encoder({"detail": error_details})
    return JSONResponse(status_code=422, content=safe_content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    #Maneja errores HTTP explícitos (404, 403)
    logger.warning(f" HTTP {exc.status_code} en {request.url}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def general_exception_handler(request: Request, exc: Exception):
    #Maneja cualquier otro error inesperado (500)
    logger.exception(f"Error inesperado en {request.url}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --- Función de Registro ---
    #Registra todos los manejadores de excepciones globales en la aplicación 

def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Manejadores de excepciones globales registrados.")