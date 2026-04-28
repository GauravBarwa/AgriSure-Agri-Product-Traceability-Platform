from pydantic import BaseModel, Field


class BuyerRaceRequest(BaseModel):
    contract_quantity: float = Field(default=1200.0, gt=0)
    price_per_kg: float = Field(default=250.0, gt=0)
    buyer_a_hold_seconds: float = Field(default=2.0, ge=0, le=10)
    buyer_b_hold_seconds: float = Field(default=0.0, ge=0, le=10)
    isolation_level: str = "SERIALIZABLE"


class InspectionRaceRequest(BaseModel):
    inspector_a_decision: str = "Approved"
    inspector_b_decision: str = "Rejected"
    inspector_a_hold_seconds: float = Field(default=2.0, ge=0, le=10)
    inspector_b_hold_seconds: float = Field(default=0.0, ge=0, le=10)
    isolation_level: str = "SERIALIZABLE"
