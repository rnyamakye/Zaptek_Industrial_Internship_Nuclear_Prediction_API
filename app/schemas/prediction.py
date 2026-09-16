from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input payload for /predict.

    NOTE: adjust the ge/le bounds once you know the real valid ranges
    the model was trained on — ask the ML sub-team.
    """

    enrichment_percent: float = Field(
        ..., gt=0, le=100, description="Uranium enrichment percentage"
    )
    fuel_density: float = Field(..., gt=0, description="Fuel density (g/cm^3)")
    moderator_density: float = Field(
        ..., gt=0, description="Moderator density (g/cm^3)"
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
    k_eff: float = Field(..., description="Predicted neutron multiplication factor")
    reactor_status: str = Field(
        ..., description="Predicted status, e.g. subcritical/critical/supercritical"
    )
    uncertainty: float | None = Field(
        None, description="Confidence/uncertainty estimate, if supported by the model"
    )
