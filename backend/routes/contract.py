from fastapi import APIRouter
import psycopg
from db import execute_query
from schemas.contract_schema import CreateContractRequest
from pydantic import BaseModel

router = APIRouter(prefix="/contract", tags=["Contract"])

class ContractConfigRequest(BaseModel):
    weight_quantity: float = 1.0
    weight_quality: float = 0.0
    bonus_threshold: float | None = None
    bonus_multiplier: float | None = None

@router.post("/create")
def create_contract(request: CreateContractRequest):
    buyer_id = request.buyer_id
    lot_id = request.lot_id
    price = request.price_per_kg
    qty = request.contract_quantity

    # -------------------------
    # 1. Validate buyer exists
    # -------------------------
    buyer = execute_query(
        "SELECT * FROM Export_Buyers WHERE UserID = %s",
        (buyer_id,),
        fetch=True
    )

    if not buyer:
        return {"error": "Buyer not found"}

    # -------------------------
    # 2. Validate lot exists
    # -------------------------
    lot = execute_query(
        "SELECT * FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    if not lot:
        return {"error": "Lot not found"}

    # -------------------------
    # 3. Check lot is approved
    # -------------------------
    if lot[0]["lotstatus"] != "Approved":
        return {"error": "Lot is not approved for sale"}

    # -------------------------
    # 4. Check already sold
    # -------------------------
    existing = execute_query(
        "SELECT * FROM Export_Contracts WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    if existing:
        return {"error": "Lot already sold"}

    # -------------------------
    # 5. Create contract
    # -------------------------
    query = """
        INSERT INTO Export_Contracts
        (BuyerID, LotID, ContractQuantityKg, PricePerKg, Status)
        VALUES (%s, %s, %s, %s, 'Active')
        RETURNING ContractID;
    """

    result = execute_query(
        query,
        (buyer_id, lot_id, qty, price),
        fetch=True
    )

    return {
        "message": "Contract created successfully",
        "contract_id": result[0]["contractid"],
        "lot_id": lot_id
    }

@router.post("/{contract_id}/config")
def create_or_update_config(contract_id: int, request: ContractConfigRequest):

    # Check contract exists
    contract = execute_query(
        "SELECT * FROM Export_Contracts WHERE ContractID = %s",
        (contract_id,),
        fetch=True
    )

    if not contract:
        return {"error": "Contract not found"}

    try:
        execute_query("""
            INSERT INTO Contract_Payout_Config (
                ContractID,
                WeightQuantity,
                WeightQuality,
                BonusThreshold,
                BonusMultiplier
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ContractID)
            DO UPDATE SET
                WeightQuantity = EXCLUDED.WeightQuantity,
                WeightQuality = EXCLUDED.WeightQuality,
                BonusThreshold = EXCLUDED.BonusThreshold,
                BonusMultiplier = EXCLUDED.BonusMultiplier;
        """, (
            contract_id,
            request.weight_quantity,
            request.weight_quality,
            request.bonus_threshold,
            request.bonus_multiplier
        ), fetch=False)
    except psycopg.errors.UndefinedTable:
        return {
            "message": "Contract payout configuration table is missing in the current database; default payout weights will be used.",
            "contract_id": contract_id
        }

    return {
        "message": "Contract payout configuration saved",
        "contract_id": contract_id
    }


# ---------------------------------------
# GET CONFIG (VERY USEFUL FOR UI)
# ---------------------------------------
@router.get("/{contract_id}/config")
def get_config(contract_id: int):

    try:
        config = execute_query("""
            SELECT *
            FROM Contract_Payout_Config
            WHERE ContractID = %s
        """, (contract_id,), fetch=True)
    except psycopg.errors.UndefinedTable:
        return {"message": "Payout configuration table not available in the current database"}

    if not config:
        return {"message": "No config found for this contract"}

    return {
        "contract_id": contract_id,
        "config": config[0]
    }


@router.get("/buyer/{buyer_id}")
def get_buyer_contracts(buyer_id: int):

    buyer = execute_query(
        "SELECT * FROM Export_Buyers WHERE UserID = %s",
        (buyer_id,),
        fetch=True
    )

    if not buyer:
        return {"error": "Buyer not found"}

    contracts = execute_query("""
        SELECT
            ec.ContractID,
            ec.LotID,
            ec.ContractQuantityKg,
            ec.PricePerKg,
            ec.Status,
            l.LotStatus,
            l.CreatedDate
        FROM Export_Contracts ec
        JOIN Aggregation_Lots l ON ec.LotID = l.LotID
        WHERE ec.BuyerID = %s
        ORDER BY ec.ContractID DESC
    """, (buyer_id,), fetch=True)

    return {
        "buyer_id": buyer_id,
        "count": len(contracts),
        "contracts": contracts
    }


@router.get("/all")
def get_all_contracts():

    contracts = execute_query("""
        SELECT
            ec.ContractID,
            ec.BuyerID,
            ec.LotID,
            ec.ContractQuantityKg,
            ec.PricePerKg,
            ec.Status,
            l.LotStatus
        FROM Export_Contracts ec
        JOIN Aggregation_Lots l ON ec.LotID = l.LotID
        ORDER BY ec.ContractID DESC
    """, fetch=True)

    return {
        "count": len(contracts),
        "contracts": contracts
    }
