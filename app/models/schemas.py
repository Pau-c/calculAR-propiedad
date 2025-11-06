from pydantic import BaseModel, Field
from typing import Optional

# modelo p/pydantic 

class Sample(BaseModel):
    lon: float = Field(..., description="Longitud geográfica")
    lat: float = Field(..., description="Latitud geográfica")
    l3: str = Field(..., description="Barrio o zona (ej: Almagro)")
    rooms: Optional[float] = Field(None, ge=0)
    bedrooms: Optional[float] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    surface_total: Optional[float] = Field(None, ge=0)
    surface_covered: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", description="Moneda de precio esperado")
    price_period: Optional[str] = Field(None, description="Periodo del precio")
    property_type: str = Field(..., description="Tipo de propiedad (ej: Departamento, PH, Casa)")
    operation_type: str = Field(..., description="Tipo de operación (Venta o Alquiler)")
    days_active: Optional[float] = Field(None, ge=0)
    created_age_days: Optional[float] = Field(None, ge=0)

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


class PredictionOut(BaseModel):
    predicted_price: float
    currency: str
    latency_ms: float
