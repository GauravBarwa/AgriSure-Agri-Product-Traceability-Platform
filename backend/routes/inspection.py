from fastapi import APIRouter
from db import execute_query
from schemas.inspection_schema import InspectionRequest

router = APIRouter(prefix="/inspection", tags=["Inspection"])

@router.post("/inspect")
def inspect_lot(request: InspectionRequest):
    lot_id = request.lot_id
    inspector_id = request.inspector_id
    decision = request.decision

    # -------------------------
    # 1. Validate decision
    # -------------------------
    if decision not in ["Approved", "Rejected"]:
        return {"error": "Invalid decision"}

    # -------------------------
    # 2. Check lot exists
    # -------------------------
    lot = execute_query(
        "SELECT * FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    if not lot:
        return {"error": "Lot not found"}

    # -------------------------
    # 3. Check inspector exists
    # -------------------------
    inspector = execute_query(
        "SELECT * FROM Quality_Inspectors WHERE UserID = %s",
        (inspector_id,),
        fetch=True
    )

    if not inspector:
        return {"error": "Inspector not found"}

    # -------------------------
    # 4. Insert inspection record
    # -------------------------
    execute_query("""
        INSERT INTO Lot_Inspections (LotID, InspectorID, InspectionDate, FinalDecision)
        VALUES (%s, %s, NOW(), %s)
    """, (lot_id, inspector_id, decision))

    # Keep the application flow consistent even if the trigger was not loaded
    # or the database was refreshed without reapplying trigger definitions.
    execute_query("""
        UPDATE Aggregation_Lots
        SET LotStatus = %s
        WHERE LotID = %s
    """, (decision, lot_id))

    lot_status = execute_query("""
    SELECT LotStatus FROM Aggregation_Lots WHERE LotID = %s
    """, (lot_id,), fetch=True)

    return {
        "message": f"Lot {decision.lower()} successfully",
        "lot_id": lot_id,
        "updated_status": lot_status[0]["lotstatus"]
    }

@router.get("/pending-lots")
def get_pending_lots():

    query = """
        SELECT 
            l.LotID,
            l.CreatedDate,
            COALESCE(SUM(lc. contributedquantitykg), 0) AS TotalWeight
        FROM Aggregation_Lots l
        LEFT JOIN Lot_Contributions lc ON l.LotID = lc.LotID
        WHERE l.LotID NOT IN (
            SELECT LotID FROM Lot_Inspections
        )
        GROUP BY l.LotID, l.CreatedDate
        ORDER BY l.CreatedDate DESC;
    """

    result = execute_query(query, fetch=True)

    return {
        "num_pending_lots": len(result),
        "lots": result
    }

@router.get("/{lot_id}")
def get_lot(lot_id: int):

    lot = execute_query("""
        SELECT LotID, LotStatus
        FROM Aggregation_Lots
        WHERE LotID = %s
    """, (lot_id,), fetch=True)

    if not lot:
        return {"error": "Lot not found"}

    return lot[0]


@router.get("/traceability/{lot_id}")
def traceability(lot_id: int):

    query = """ WITH lot_base AS (
    SELECT 
        ec.ContractID,
        ec.BuyerID,
        ec.LotID,
        ec.ContractQuantityKg,
        ec.PricePerKg
    FROM Export_Contracts ec
    WHERE ec.LotID = %s
),

contributions AS (
    SELECT 
        lc.LotID,
        lc.HarvestID,
        lc.ContributedQuantityKg,
        lc.QualityScore,
        hs.FarmerID,
        hs.CycleID
    FROM Lot_Contributions lc
    JOIN Harvest_Submissions hs ON lc.HarvestID = hs.HarvestID
    WHERE lc.LotID = %s
),

farmer_info AS (
    SELECT 
        f.UserID AS FarmerID,
        ua.Username,
        f.FarmerStatus
    FROM Farmers f
    JOIN User_Accounts ua ON f.UserID = ua.UserID
),

parcel_info AS (
    SELECT 
        lp.ParcelID,
        lp.FarmerID,
        lp.LocationCoordinates,
        lp.AreaHectares
    FROM Land_Parcels lp
),

cycle_info AS (
    SELECT 
        cc.CycleID,
        cc.ParcelID,
        cc.CropID,
        cc.Status
    FROM Crop_Cycles cc
),

sensor_summary AS (
    SELECT 
        s.ParcelID,
        AVG(sr.SoilPH) AS avg_ph,
        AVG(sr.Moisture) AS avg_moisture,
        AVG(sr.Temperature) AS avg_temp
    FROM Sensors s
    JOIN Sensor_Readings sr ON s.SensorID = sr.SensorID
    GROUP BY s.ParcelID
)

SELECT 
    lb.ContractID,
    lb.BuyerID,
    c.FarmerID,
    fi.Username,
    c.ContributedQuantityKg,
    c.QualityScore,
    pi.ParcelID,
    pi.LocationCoordinates,
    ci.CycleID,
    ci.Status AS CycleStatus,
    ss.avg_ph,
    ss.avg_moisture,
    ss.avg_temp

FROM lot_base lb
JOIN contributions c ON lb.LotID = c.LotID
JOIN farmer_info fi ON c.FarmerID = fi.FarmerID
JOIN cycle_info ci ON c.CycleID = ci.CycleID
JOIN parcel_info pi ON ci.ParcelID = pi.ParcelID
LEFT JOIN sensor_summary ss ON pi.ParcelID = ss.ParcelID;"""

    result = execute_query(query, (lot_id, lot_id), fetch=True)

    if not result:
        return {"error": "No traceability data found"}

    return {
        "lot_id": lot_id,
        "traceability": result
    }
