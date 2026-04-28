----TRIGGER 1: At Risk trigger -------- 

-- Create crop
INSERT INTO Crops (CropName, Variety, IdealSoilPH, IdealMoisture)
VALUES ('Wheat', 'Wheat-A', 6.5, 50);

-- Create user + farmer
INSERT INTO User_Accounts (Username, PasswordHash, Email, RoleType)
VALUES ('farmer1', 'hash', 'f1@mail.com', 'Farmer');

INSERT INTO Farmers (UserID, RegistrationDate)
VALUES (1, CURRENT_DATE);

-- Create parcel
INSERT INTO Land_Parcels (FarmerID, LocationCoordinates, AreaHectares)
VALUES (1, 'Location', 2.5);

-- Create crop cycle
INSERT INTO Crop_Cycles (ParcelID, CropID, StartDate)
VALUES (1, 1, CURRENT_DATE);

-- Create sensor
INSERT INTO Sensors (ParcelID, SensorType)
VALUES (1, 'Soil');



--Testing
INSERT INTO Sensor_Readings (SensorID, ReadingTimestamp, SoilPH, Moisture)
VALUES (1, CURRENT_TIMESTAMP, 6.5, 50);

INSERT INTO Sensor_Readings (SensorID, ReadingTimestamp, SoilPH, Moisture)
VALUES (1, CURRENT_TIMESTAMP + INTERVAL '1 second', 10, 90);

SELECT Status FROM Crop_Cycles;



---- Trigger 2: Update Lot Status Trigger ------

INSERT INTO Aggregation_Lots (LotStatus)
VALUES ('Open')
RETURNING LotID;

SELECT LotID, LotStatus
FROM Aggregation_Lots
WHERE LotID = 1;

INSERT INTO Lot_Inspections (
    LotID,
    InspectorID,
    FinalDecision
)
VALUES (
    1,          -- your LotID
    3,        -- must exist in Quality_Inspectors
    'Approved'  -- try Approved / Rejected / Reclassified
);

INSERT INTO Lot_Inspections (LotID, InspectorID, FinalDecision)
VALUES (1, 3, 'Rejected');

SELECT LotID, LotStatus
FROM Aggregation_Lots
WHERE LotID = 1;