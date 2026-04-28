from pydantic import BaseModel

class CreatePaymentRequest(BaseModel):
    contract_id: int