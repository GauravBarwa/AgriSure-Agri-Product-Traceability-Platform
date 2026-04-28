from pydantic import BaseModel

class CreateContractRequest(BaseModel):
    buyer_id: int
    lot_id: int
    price_per_kg: float
    contract_quantity: float