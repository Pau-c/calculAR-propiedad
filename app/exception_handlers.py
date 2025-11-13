from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from app.utils.log_config import logger

# Manejo de importación opcional de Datadog
try:
    from ddtrace import tracer
except ImportError:
    tracer = None

# --- MANEJO DE ERRORES ---

async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de la request de FastAPI/Pydantic (422)."""
    error_details = exc.errors()
    error_source = "FastAPI Request"

    logger.warning(f"Error de validación ({error_source}) en {request.url}: {error_details}")
    
    if tracer:
        span = tracer.current_span()
        if span:
            span.set_tag("validation.error_source", error_source)
            span.set_tag("validation.error_count", len(error_details))
            span.set_tag("request.url", str(request.url))
    
    # SOLUCIÓN: Usar jsonable_encoder para asegurar que los errores sean serializables
    safe_content = jsonable_encoder({"detail": error_details})
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=safe_content)


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Maneja errores de validación interna de Pydantic """
    error_details = exc.errors()
    error_source = "Pydantic Interna"

    logger.error(f"Error de validación ({error_source}) en {request.url}: {error_details}")
    
    if tracer:
        span = tracer.current_span()
        if span:
            span.set_tag("validation.error_source", error_source)
            span.set_tag("validation.error_count", len(error_details))
            span.set_tag("request.url", str(request.url))
  
    safe_content = jsonable_encoder({"detail": error_details})
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=safe_content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja errores HTTP explícitos (404, 403) lanzados con raise HTTPException."""
    logger.warning(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def general_exception_handler(request: Request, exc: Exception):
    """Maneja cualquier error inesperado (500)."""
    logger.exception(f"Error inesperado (500) en {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
        content={"detail": "Error interno del servidor", "error": str(exc)}
    )


# --- Función de Registro ---
def register_exception_handlers(app: FastAPI):
    """Registra todos los manejadores de excepciones globales en la aplicación."""
    
    # Este es el manejador principal para errores de validación de Pydantic
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    
    # Manejador para validaciones de Pydantic (si se usan manualmente)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Manejador para errores HTTP (ej. 404 Not Found)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Manejador genérico para errores 500
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Manejadores de excepciones globales registrados.")