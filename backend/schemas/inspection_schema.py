from pydantic import BaseModel

class InspectionRequest(BaseModel):
    lot_id: int
    inspector_id: int
    decision: str  # "Approved" or "Rejected"