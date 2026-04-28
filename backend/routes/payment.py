from fastapi import APIRouter
import psycopg
from db import execute_query
from schemas.payment_schema import CreatePaymentRequest

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/create")
def create_payment(request: CreatePaymentRequest):

    contract_id = request.contract_id

    # -------------------------
    # 1. Get contract
    # -------------------------
    contract = execute_query(
        "SELECT * FROM Export_Contracts WHERE ContractID = %s",
        (contract_id,),
        fetch=True
    )

    if not contract:
        return {"error": "Contract not found"}

    contract = contract[0]
    lot_id = contract["lotid"]
    qty = contract["contractquantitykg"]
    price = contract["priceperkg"]

    total_amount = qty * price

    # -------------------------
    # 2. Create payment
    # -------------------------
    payment_result = execute_query("""
        INSERT INTO Payments (ContractID, TotalAmount, PaymentDate)
        VALUES (%s, %s, NOW())
        RETURNING PaymentID;
    """, (contract_id, total_amount), fetch=True)

    payment_id = payment_result[0]["paymentid"]

    # -------------------------
    # 2.5 Get payout config
    # -------------------------
    try:
        config = execute_query("""
            SELECT *
            FROM Contract_Payout_Config
            WHERE ContractID = %s
        """, (contract_id,), fetch=True)
    except psycopg.errors.UndefinedTable:
        config = None

    if config:
        config = config[0]
        weight_qty = config["weightquantity"]
        weight_quality = config["weightquality"]
        bonus_threshold = config.get("bonusthreshold")
        bonus_multiplier = config.get("bonusmultiplier")
    else:
        weight_qty = 1
        weight_quality = 0
        bonus_threshold = None
        bonus_multiplier = None

    # -------------------------
    # 3. Get contributions
    # -------------------------
    contributions = execute_query("""
        SELECT 
            lc.ContributedQuantityKg,
            lc.QualityScore,
            hs.FarmerID
        FROM Lot_Contributions lc
        JOIN Harvest_Submissions hs ON lc.HarvestID = hs.HarvestID
        WHERE lc.LotID = %s
    """, (lot_id,), fetch=True)

    if not contributions:
        return {"error": "No contributions found for this lot"}

    # -------------------------
    # 4. Compute weights
    # -------------------------
    total_weight = 0

    for c in contributions:
        qty = c["contributedquantitykg"]
        quality = c.get("qualityscore") or 1

        weight = (qty * weight_qty) + (quality * weight_quality)

        # bonus logic
        if bonus_threshold and bonus_multiplier:
            if quality >= bonus_threshold:
                weight *= bonus_multiplier

        c["weight"] = weight
        total_weight += weight

    if total_weight == 0:
        return {"error": "Invalid contribution weights"}

    # -------------------------
    # 5. Generate payouts
    # -------------------------
    payouts = []

    for c in contributions:
        farmer_id = c["farmerid"]
        weight = c["weight"]

        payout_amount = (weight / total_weight) * total_amount

        execute_query("""
            INSERT INTO Farmer_Payouts (PaymentID, FarmerID, Amount)
            VALUES (%s, %s, %s)
        """, (payment_id, farmer_id, payout_amount), fetch=False)

        payouts.append({
            "farmer_id": farmer_id,
            "amount": payout_amount
        })

    return {
        "message": "Payment created and distributed",
        "payment_id": payment_id,
        "total_amount": total_amount,
        "payouts": payouts
    }

@router.get("/{contract_id}/payouts")
def get_payouts(contract_id: int):

    result = execute_query("""
        SELECT 
            fp.FarmerID,
            fp.Amount,
            fp.PaymentID
        FROM Farmer_Payouts fp
        JOIN Payments p ON fp.PaymentID = p.PaymentID
        WHERE p.ContractID = %s
    """, (contract_id,), fetch=True)

    return {
        "contract_id": contract_id,
        "payouts": result
    }
