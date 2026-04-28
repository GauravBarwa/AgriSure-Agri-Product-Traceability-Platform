from fastapi import APIRouter

from schemas.transaction_demo_schema import BuyerRaceRequest, InspectionRaceRequest
from services.transaction_demo import (
    ensure_demo_participants,
    simulate_buyer_race,
    simulate_inspection_race,
)

router = APIRouter(prefix="/transaction-demo", tags=["Transaction Demo"])


@router.get("/participants")
def get_demo_participants():
    return ensure_demo_participants()


@router.post("/double-sale")
def run_double_sale(request: BuyerRaceRequest):
    return simulate_buyer_race(
        contract_quantity=request.contract_quantity,
        price_per_kg=request.price_per_kg,
        buyer_a_hold_seconds=request.buyer_a_hold_seconds,
        buyer_b_hold_seconds=request.buyer_b_hold_seconds,
        isolation_level=request.isolation_level,
    )


@router.post("/double-inspection")
def run_double_inspection(request: InspectionRaceRequest):
    return simulate_inspection_race(
        inspector_a_decision=request.inspector_a_decision,
        inspector_b_decision=request.inspector_b_decision,
        inspector_a_hold_seconds=request.inspector_a_hold_seconds,
        inspector_b_hold_seconds=request.inspector_b_hold_seconds,
        isolation_level=request.isolation_level,
    )
