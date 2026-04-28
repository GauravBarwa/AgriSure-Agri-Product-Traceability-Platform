from pydantic import BaseModel
from typing import Dict

class AddParcelRequest(BaseModel):
    farmer_id: int
    location_coordinates: str
    area_hectares: float
    elevation_msl: float
    soil_baseline_json: Dict
    certification_status: str