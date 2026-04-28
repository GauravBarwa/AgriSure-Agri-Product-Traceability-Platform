-- 1. List all registered farmers
SELECT u.UserID, u.Username, f.RegistrationDate, f.FarmerStatus
FROM User_Accounts u
JOIN Farmers f ON u.UserID = f.UserID;

-- 2. Find all land parcels owned by farmers
SELECT f.UserID AS FarmerID, u.Username, l.ParcelID, l.AreaHectares
FROM Farmers f
JOIN User_Accounts u ON f.UserID = u.UserID
JOIN Land_Parcels l ON f.UserID = l.FarmerID;

-- 3. List active crop cycles
SELECT c.CycleID, cr.CropName, cr.Variety, c.StartDate, c.Status
FROM Crop_Cycles c
JOIN Crops cr ON c.CropID = cr.CropID
WHERE c.Status = 'Active';

-- 4. Retrieve sensor readings for a specific parcel
SELECT s.SensorID, sr.ReadingTimestamp, sr.SoilPH, sr.Moisture
FROM Sensors s
JOIN Sensor_Readings sr ON s.SensorID = sr.SensorID
WHERE s.ParcelID = 1;

-- 5. Calculate daily average soil moisture
SELECT
DATE(ReadingTimestamp) AS Day,
AVG(Moisture) AS AvgMoisture
FROM Sensor_Readings
GROUP BY DATE(ReadingTimestamp)
ORDER BY Day;

-- 6. Find parcels where moisture exceeds crop ideal levels
SELECT l.ParcelID, sr.Moisture, c.IdealMoisture
FROM Land_Parcels l
JOIN Crop_Cycles cc ON l.ParcelID = cc.ParcelID
JOIN Crops c ON cc.CropID = c.CropID
JOIN Sensors s ON s.ParcelID = l.ParcelID
JOIN Sensor_Readings sr ON sr.SensorID = s.SensorID
WHERE sr.Moisture > c.IdealMoisture;

-- 7. Total harvest contributed by each farmer
SELECT FarmerID, SUM(QuantityKg) AS TotalHarvest
FROM Harvest_Submissions
GROUP BY FarmerID;

-- 8. View contribution of farmers to each aggregation lot
SELECT
lc.LotID,
h.FarmerID,
lc.ContributedQuantityKg
FROM Lot_Contributions lc
JOIN Harvest_Submissions h
ON lc.HarvestID = h.HarvestID;

-- 9. Show inspection results for lots
SELECT
l.LotID,
li.InspectionDate,
li.FinalDecision,
qi.Organization
FROM Lot_Inspections li
JOIN Aggregation_Lots l ON li.LotID = l.LotID
JOIN Quality_Inspectors qi ON li.InspectorID = qi.UserID;

-- 10. Find all approved lots ready for export
SELECT LotID, CreatedDate
FROM Aggregation_Lots
WHERE LotStatus = 'Approved';

-- 11. Retrieve buyer contracts with pricing
SELECT
ec.ContractID,
u.Username AS Buyer,
ec.ContractQuantityKg,
ec.PricePerKg
FROM Export_Contracts ec
JOIN Export_Buyers b ON ec.BuyerID = b.UserID
JOIN User_Accounts u ON b.UserID = u.UserID;

-- 12. Calculate total contract value
SELECT
ContractID,
ContractQuantityKg,
PricePerKg,
(ContractQuantityKg * PricePerKg) AS ContractValue
FROM Export_Contracts;

-- 13. Revenue distributed to each farmer
SELECT
FarmerID,
SUM(Amount) AS TotalPayout
FROM Farmer_Payouts
GROUP BY FarmerID;

-- 14. Traceavility query (Buyer -> Lot -> Farmer)
SELECT
ec.ContractID,
ec.LotID,
h.FarmerID,
lc.ContributedQuantityKg
FROM Export_Contracts ec
JOIN Lot_Contributions lc ON ec.LotID = lc.LotID
JOIN Harvest_Submissions h ON lc.HarvestID = h.HarvestID;

-- 15. Rank farmers by contribution quantity
SELECT
FarmerID,
SUM(QuantityKg) AS TotalHarvest,
RANK() OVER (ORDER BY SUM(QuantityKg) DESC) AS Rank
FROM Harvest_Submissions
GROUP BY FarmerID;
