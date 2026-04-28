from pydantic import BaseModel
from typing import List

class LotCreateRequest(BaseModel):
    harvest_ids: List[int]