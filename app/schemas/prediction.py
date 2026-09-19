from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    # Input payload for /predict.

    # Bounds match the trained model's actual training_data_range.

    enrichment_percent: float = Field(
        ..., ge=2.0, le=5.0, description="Uranium enrichment percentage (valid range 2-5%)"
    )
    fuel_density: float = Field(
        ..., ge=9.80, le=10.60, description="Fuel density in g/cm^3 (valid range 9.80-10.60)"
    )
    moderator_density: float = Field(
        ..., ge=0.95, le=1.05, description="Moderator density in g/cm^3 (valid range 0.95-1.05)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enrichment_percent": 4.5,
                "fuel_density": 10.2,
                "moderator_density": 0.98,
            }
        }


class PredictionResponse(BaseModel):
    k_eff: float = Field(...,
                         description="Predicted neutron multiplication factor")
    reactor_status: str = Field(
        ..., description="Predicted status: Subcritical, Critical, or Supercritical"
    )
    uncertainty: float | None = Field(
        None, description="Std. deviation of predictions across the forest's trees"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "k_eff": 1.02,
                "reactor_status": "Critical",
                "uncertainty": 0.009
            }
        }
