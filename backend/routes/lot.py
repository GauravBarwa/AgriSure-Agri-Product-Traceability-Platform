from fastapi import APIRouter
from db import execute_query
from schemas.lot_schema import LotCreateRequest

router = APIRouter(prefix="/lot", tags=["Lot"])


@router.post("/create")
def create_lot(request: LotCreateRequest):

    harvest_ids = request.harvest_ids

    if not harvest_ids:
        return {"error": "No harvest IDs provided"}

    # Validate harvests exist
    query = """
        SELECT HarvestID, QuantityKg
        FROM Harvest_Submissions
        WHERE HarvestID = ANY(%s)
    """

    harvests = execute_query(query, (harvest_ids,), fetch=True)

    if len(harvests) != len(harvest_ids): # type: ignore
        return {"error": "Some harvest IDs are invalid"}

    # Check already assigned
    assigned = execute_query("""
        SELECT HarvestID FROM Lot_Contributions
        WHERE HarvestID = ANY(%s)
    """, (harvest_ids,), fetch=True)

    if assigned:
        return {"error": "Some harvests already assigned"}

    # Create lot
    lot_result = execute_query("""
        INSERT INTO Aggregation_Lots (LotStatus, CreatedDate)
        VALUES ('Open', NOW())
        RETURNING LotID;
    """, fetch=True)

    lot_id = lot_result[0]["lotid"] # type: ignore

    total_qty = 0

    for h in harvests: # type: ignore
        qty = h["quantitykg"]
        total_qty += qty

        execute_query("""
            INSERT INTO Lot_Contributions (LotID, HarvestID, ContributedQuantityKg)
            VALUES (%s, %s, %s)
        """, (lot_id, h["harvestid"], qty))

    return {
        "message": "Lot created successfully",
        "lot_id": lot_id,
        "total_quantity": total_qty
    }


@router.get("/available-harvests")
def get_available_harvests():

    query = """
        SELECT
            hs.HarvestID,
            hs.FarmerID,
            hs.CycleID,
            hs.QuantityKg,
            hs.SubmissionDate,
            c.CropName
        FROM Harvest_Submissions hs
        JOIN Crop_Cycles cc ON hs.CycleID = cc.CycleID
        JOIN Crops c ON cc.CropID = c.CropID
        WHERE hs.HarvestID NOT IN (
            SELECT HarvestID FROM Lot_Contributions
        )
        ORDER BY hs.SubmissionDate DESC;
    """

    harvests = execute_query(query, fetch=True)

    return {
        "count": len(harvests),
        "harvests": harvests
    }


@router.get("/approved")
def get_approved_lots():

    query = """
        SELECT
            l.LotID,
            l.LotStatus,
            l.CreatedDate,
            COALESCE(SUM(lc.ContributedQuantityKg), 0) AS TotalWeight,
            COUNT(DISTINCT hs.FarmerID) AS FarmerCount
        FROM Aggregation_Lots l
        LEFT JOIN Lot_Contributions lc ON l.LotID = lc.LotID
        LEFT JOIN Harvest_Submissions hs ON lc.HarvestID = hs.HarvestID
        WHERE l.LotStatus = 'Approved'
          AND l.LotID NOT IN (
              SELECT LotID FROM Export_Contracts
          )
        GROUP BY l.LotID, l.LotStatus, l.CreatedDate
        HAVING COALESCE(SUM(lc.ContributedQuantityKg), 0) > 0
        ORDER BY l.CreatedDate DESC;
    """

    lots = execute_query(query, fetch=True)

    return {
        "count": len(lots),
        "lots": lots
    }


@router.get("/{lot_id}")
def get_lot(lot_id: int):

    lot = execute_query(
        """
        SELECT LotID, LotStatus, CreatedDate
        FROM Aggregation_Lots
        WHERE LotID = %s
        """,
        (lot_id,),
        fetch=True
    )

    if not lot:
        return {"error": "Lot not found"}

    return lot[0]


@router.get("/all")
def get_all_lot_inspections():

    query = """
        SELECT 
            InspectionID,
            LotID,
            InspectorID,
            InspectionDate,
            PhysicalResult,
            FinalDecision
        FROM Lot_Inspections
        ORDER BY InspectionDate DESC;
    """

    inspections = execute_query(query, fetch=True)

    return {
        "count": len(inspections), # type: ignore
        "data": inspections
    }


@router.get("/{lot_id}/contributions")
def get_lot_contributions(lot_id: int):

    # 1. Validate lot exists
    lot = execute_query(
        "SELECT * FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    if not lot:
        return {"error": "Lot not found"}

    # 2. Fetch contributions
    query = """
        SELECT 
            lc.ContributionID,
            lc.HarvestID,
            lc.ContributedQuantityKg,
            lc.QualityScore,

            hs.FarmerID,
            hs.CycleID

        FROM Lot_Contributions lc
        JOIN Harvest_Submissions hs ON lc.HarvestID = hs.HarvestID

        WHERE lc.LotID = %s
        ORDER BY lc.ContributionID;
    """

    contributions = execute_query(query, (lot_id,), fetch=True)

    if not contributions:
        return {
            "lot_id": lot_id,
            "num_contributions": 0,
            "total_quantity": 0,
            "contributions": []
        }

    # 3. Compute totals
    total_qty = sum(c["contributedquantitykg"] for c in contributions)

    for c in contributions:
        c["contribution_percent"] = round(
            (c["contributedquantitykg"] / total_qty) * 100, 2
        )

    return {
        "lot_id": lot_id,
        "num_contributions": len(contributions),
        "total_quantity": total_qty,
        "contributions": contributions
    }

@router.get("/{lot_id}/trace")
def trace_lot(lot_id: int):

    # -------------------------
    # 1. Validate lot exists
    # -------------------------
    lot = execute_query(
        "SELECT * FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    if not lot:
        return {"error": "Lot not found"}

    lot = lot[0]

    # -------------------------
    # 2. Contribution chain
    # -------------------------
    query = """
        SELECT 
            lc.ContributedQuantityKg,
            lc.QualityScore,
            hs.HarvestID,
            hs.FarmerID,
            hs.SubmissionDate,
            hs.CycleID,

            lp.ParcelID,
            lp.LocationCoordinates,

            cc.Status AS CycleStatus,

            c.CropName

        FROM Lot_Contributions lc
        JOIN Harvest_Submissions hs ON lc.HarvestID = hs.HarvestID
        JOIN Crop_Cycles cc ON cc.CycleID = hs.CycleID
        JOIN Land_Parcels lp ON cc.ParcelID = lp.ParcelID
        JOIN Crops c ON cc.CropID = c.CropID

        WHERE lc.LotID = %s
    """

    chain = execute_query(query, (lot_id,), fetch=True)

    # -------------------------
    # 3. Compute totals + %
    # -------------------------
    total_qty = sum(r["contributedquantitykg"] for r in chain)

    contributions = []
    farmers = {}
    parcels = {}

    for r in chain:
        farmer_id = r["farmerid"]
        parcel_id = r["parcelid"]
        qty = r["contributedquantitykg"]

        percent = (qty / total_qty) * 100 if total_qty > 0 else 0

        contributions.append({
            "farmer_id": farmer_id,
            "harvest_id": r["harvestid"],
            "quantity": qty,
            "contribution_percent": round(percent, 2)
        })

        # aggregate farmer totals
        if farmer_id not in farmers:
            farmers[farmer_id] = {
                "farmer_id": farmer_id,
                "total_contribution": 0
            }

        farmers[farmer_id]["total_contribution"] += qty

        # parcel info
        if parcel_id not in parcels:
            parcels[parcel_id] = {
                "parcel_id": parcel_id,
                "location": r["locationcoordinates"],
                "crop": r["cropname"]
            }

    # -------------------------
    # 4. Sensor Summary (latest)
    # -------------------------
    sensor_query = """
        SELECT 
            s.SensorID,
            s.ParcelID,
            sr.Moisture,
            sr.SoilPH,
            sr.ReadingTimestamp

        FROM Sensors s
        JOIN Sensor_Readings sr ON sr.SensorID = s.SensorID
        WHERE sr.ReadingTimestamp = (
            SELECT MAX(sr2.ReadingTimestamp)
            FROM Sensor_Readings sr2
            WHERE sr2.SensorID = s.SensorID
        )
        AND s.ParcelID IN (
            SELECT cc.ParcelID
            FROM Harvest_Submissions hs
            JOIN Crop_Cycles cc ON hs.CycleID = cc.CycleID
            JOIN Lot_Contributions lc ON lc.HarvestID = hs.HarvestID
            WHERE lc.LotID = %s
        )
    """

    sensors = execute_query(sensor_query, (lot_id,), fetch=True)

    # -------------------------
    # 5. Timeline (NEW FEATURE 🔥)
    # -------------------------

    # Harvest timestamps
    harvest_times = [r["submissiondate"] for r in chain if r["submissiondate"]]

    harvest_time = min(harvest_times) if harvest_times else None

    # Lot creation
    lot_created = lot["createddate"]

    # Inspection timestamp
    inspection = execute_query(
        "SELECT InspectionDate, FinalDecision FROM Lot_Inspections WHERE LotID = %s",
        (lot_id,),
        fetch=True
    )

    inspection_time = inspection[0]["inspectiondate"] if inspection else None
    inspection_result = inspection[0]["finaldecision"] if inspection else None

    # Payment timestamp (via contract)
    payment = execute_query("""
        SELECT p.PaymentDate
        FROM Payments p
        JOIN Export_Contracts ec ON p.ContractID = ec.ContractID
        WHERE ec.LotID = %s
    """, (lot_id,), fetch=True)

    payment_time = payment[0]["paymentdate"] if payment else None

    timeline = []

    if harvest_time:
        timeline.append({"stage": "Harvest", "time": harvest_time})

    if lot_created:
        timeline.append({"stage": "Lot Created", "time": lot_created})

    if inspection_time:
        timeline.append({
            "stage": f"Inspection ({inspection_result})",
            "time": inspection_time
        })

    if payment_time:
        timeline.append({"stage": "Payment Completed", "time": payment_time})

    # -------------------------
    # 6. Final Response
    # -------------------------
    return {
        "lot_id": lot_id,
        "lot_status": lot["lotstatus"],
        "total_quantity": total_qty,

        "timeline": timeline,                 # ✅ NEW
        "contributions": contributions,       # ✅ IMPROVED

        "farmers": list(farmers.values()),
        "parcels": list(parcels.values()),
        "sensor_summary": sensors
    }
