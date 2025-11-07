from pydantic import BaseModel, Field, field_validator

from typing import Optional

# modelo p/pydantic
class Sample(BaseModel):
    # obligatorias(mayor importancia)
    surface_total: float = Field(..., ge=0, description="Superficie total en m²")
    property_type: str = Field(..., description="Tipo de propiedad (ej: Departamento, PH, Casa)")
    operation_type: str = Field(..., description="Tipo de operación (Venta o Alquiler)")
    currency: str = Field("USD", description="Moneda (USD, ARS, etc.)")

 # opcionales
    surface_covered: Optional[float] = Field(None, ge=0)
    rooms: Optional[float] = Field(None, ge=0)
    bedrooms: Optional[float] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    l3: Optional[str] = Field(None, description="Barrio o zona (ej: Almagro)")
    lon: Optional[float] = Field(None, description="Longitud geográfica")
    lat: Optional[float] = Field(None, description="Latitud geográfica")
    price_period: Optional[str] = Field(None)
    days_active: Optional[float] = Field(None, ge=0)
    created_age_days: Optional[float] = Field(None, ge=0)


# Validadores de datos
    @field_validator("surface_covered")
    def check_surface_covered(cls, v, info):
        total = info.data.get("surface_total")
        if v is not None and total is not None and v > total:
            raise ValueError(
                "La superficie cubierta no puede superar la total."
            )
        return v

    @field_validator("property_type")
    def validate_property_type(cls, v):
        allowed = {"Departamento", "PH", "Casa"}
        if v not in allowed:
            raise ValueError(
                f"Tipo de propiedad inválido: {v}. Debe ser uno de {allowed}."
            )
        return v

    @field_validator("operation_type")
    def validate_operation_type(cls, v):
        allowed = {"Venta", "Alquiler"}
        if v not in allowed:
            raise ValueError(
                f"Tipo de operación inválido: {v}. Debe ser 'Venta' o 'Alquiler'."
            )
        return v

    @field_validator("lon", "lat")
    def validate_coordinates(cls, v, info):
        if v is not None:
            if info.field_name == "lon" and not (-65 <= v <= -55):
                raise ValueError("Longitud fuera del rango esperado para Argentina.")
            if info.field_name == "lat" and not (-40 <= v <= -20):
                raise ValueError("Latitud fuera del rango esperado para Argentina.")
        return v

# ejemplo de datos para swagger
    model_config = {
        "json_schema_extra": {
            "example": {
                "lon": -58.42,
                "lat": -34.61,
                "l3": "Almagro",
                "rooms": 3,
                "bedrooms": 1,
                "bathrooms": 1,
                "surface_total": 100,
                "surface_covered": 50,
                "currency": "USD",
                "property_type": "Departamento",
                "operation_type": "Venta",
            }
        }
    }

# response
class PredictionOut(BaseModel):
    predicted_price: float
    currency: str
    latency_ms: float
