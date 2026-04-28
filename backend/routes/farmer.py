from fastapi import APIRouter
from db import execute_query
from schemas.farmer_schema import AddParcelRequest
import json

router = APIRouter(prefix="/farmer", tags=["Farmer"])

@router.post("/harvest")
def submit_harvest(cycle_id: int, farmer_id: int, quantity: float):
    query = """
        INSERT INTO Harvest_Submissions
        (CycleID, FarmerID, QuantityKg, SubmissionDate)
        VALUES (%s, %s, %s, NOW())
        RETURNING HarvestID;
    """

    result = execute_query(query, (cycle_id, farmer_id, quantity), fetch=True)

    if result is not None:
        return {
            "message": "Harvest submitted",
            "harvest_id": result[0]["harvestid"]
        }
    # else:
    #     return {
    #         "message": "Failed to submit harvest"
    #     }



@router.get("/all_farmers")
def get_all_farmers():
    query = """
        SELECT a.userid, a.username, a.email, a.roletype
        FROM farmers f
        JOIN user_accounts a ON f.userid = a.userid
    """

    result = execute_query(query, fetch=True)

    return result

@router.post("/add-parcel")
def add_parcel(request: AddParcelRequest):

    # -------------------------
    # 1. Validate farmer exists
    # -------------------------
    farmer = execute_query(
        "SELECT * FROM Farmers WHERE UserID = %s",
        (request.farmer_id,),
        fetch=True
    )

    if not farmer:
        return {"error": "Farmer not found"}

    # -------------------------
    # 2. Insert parcel
    # -------------------------
    query = """
        INSERT INTO Land_Parcels
        (FarmerID, LocationCoordinates, AreaHectares, ElevationMSL, SoilBaselineJSON, CertificationStatus)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING ParcelID;
    """

    result = execute_query(
        query,
        (
            request.farmer_id,
            request.location_coordinates,
            request.area_hectares,
            request.elevation_msl,
            json.dumps(request.soil_baseline_json),  # store as JSON string
            request.certification_status
        ),
        fetch=True
    )

    return {
        "message": "Parcel added successfully",
        "parcel_id": result[0]["parcelid"]
    }

@router.get("/crop-cycles/{farmer_id}")
def get_crop_cycles(farmer_id: int):

    query = """
        SELECT 
            cc.CycleID,
            cc.Status,
            cc.StartDate,
            cc.EndDate,
            lp.ParcelID,
            c.CropName
        FROM Crop_Cycles cc
        JOIN Land_Parcels lp ON cc.ParcelID = lp.ParcelID
        JOIN Crops c ON cc.CropID = c.CropID
        WHERE lp.FarmerID = %s
        ORDER BY cc.StartDate DESC;
    """

    result = execute_query(query, (farmer_id,), fetch=True)

    if not result:
        return {"message": "No crop cycles found"}

    return {
        "farmer_id": farmer_id,
        "num_cycles": len(result),
        "cycles": result
    }

@router.get("/sensor-status/{farmer_id}")
def get_sensor_status(farmer_id: int):

    query = """
        SELECT 
            lp.ParcelID,
            s.SensorID,
            sr.Moisture,
            sr.SoilPH,
            sr.ReadingTimestamp
        FROM Land_Parcels lp
        JOIN Sensors s ON lp.ParcelID = s.ParcelID
        JOIN Sensor_Readings sr ON sr.SensorID = s.SensorID
        WHERE lp.FarmerID = %s
        AND sr.ReadingTimestamp = (
            SELECT MAX(sr2.ReadingTimestamp)
            FROM Sensor_Readings sr2
            WHERE sr2.SensorID = s.SensorID
        );
    """

    result = execute_query(query, (farmer_id,), fetch=True)

    if not result:
        return {"message": "No sensor data available"}

    # -------------------------
    # Add simple risk logic
    # -------------------------
    for r in result:
        if r["moisture"] < 10:
            r["status"] = "Low Moisture"
        elif r["moisture"] > 15:
            r["status"] = "High Moisture"
        else:
            r["status"] = "Healthy"

    return {
        "farmer_id": farmer_id,
        "sensor_summary": result
    }

@router.get("/parcels/{farmer_id}")
def get_farmer_parcels(farmer_id: int):

    # -------------------------
    # 1. Validate farmer exists
    # -------------------------
    farmer = execute_query(
        "SELECT * FROM Farmers WHERE UserID = %s",
        (farmer_id,),
        fetch=True
    )

    if not farmer:
        return {"error": "Farmer not found"}

    # -------------------------
    # 2. Fetch parcels
    # -------------------------
    query = """
        SELECT 
            ParcelID,
            LocationCoordinates,
            AreaHectares,
            ElevationMSL,
            SoilBaselineJSON,
            CertificationStatus
        FROM Land_Parcels
        WHERE FarmerID = %s
        ORDER BY ParcelID;
    """

    parcels = execute_query(query, (farmer_id,), fetch=True)

    return {
        "farmer_id": farmer_id,
        "num_parcels": len(parcels),
        "parcels": parcels
    }
