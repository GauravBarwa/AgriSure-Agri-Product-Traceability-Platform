INSERT INTO User_Accounts (Username, PasswordHash, Email, RoleType)
VALUES
('farmer_raj', 'hash1', 'raj@agrisure.com', 'Farmer'),
('farmer_anita', 'hash2', 'anita@agrisure.com', 'Farmer'),
('inspector_kumar', 'hash3', 'kumar@agrisure.com', 'Inspector'),
('buyer_globalex', 'hash4', 'contact@globalex.com', 'Buyer'),
('admin_main', 'hash5', 'admin@agrisure.com', 'Admin');

-- Farmers
INSERT INTO Farmers (UserID, RegistrationDate)
VALUES
(1, '2024-01-10'),
(2, '2024-02-15');

-- Inspector
INSERT INTO Quality_Inspectors (UserID, CertificationLevel, Organization)
VALUES
(3, 'Level-2 Export Certification', 'AgriCert India');

-- Buyer
INSERT INTO Export_Buyers (UserID, CompanyName, Country, ContactInfo)
VALUES
(4, 'Global Exports Ltd', 'Germany', 'Berlin HQ');

-- Admin
INSERT INTO Coop_Admins (UserID, AdminLevel)
VALUES
(5, 1);

INSERT INTO Crops (CropName, Variety, IdealSoilPH, IdealMoisture, IdealTemperature)
VALUES
('Coffee', 'Arabica Premium', 6.50, 12.00, 22.00),
('Spice', 'Black Pepper Export', 6.00, 14.00, 28.00);

-- main stuff, that has no fk constraints
INSERT INTO Land_Parcels 
(FarmerID, LocationCoordinates, AreaHectares, ElevationMSL, SoilBaselineJSON, CertificationStatus)
VALUES
(1, '12.9716N,77.5946E', 2.50, 920, '{"nitrogen":"medium","organic_matter":"high"}', 'Organic'),
(2, '11.0168N,76.9558E', 3.20, 450, '{"nitrogen":"high","organic_matter":"medium"}', 'Export-Grade');

INSERT INTO Crop_Cycles 
(ParcelID, CropID, StartDate, Status)
VALUES
(1, 1, '2025-01-01', 'Active'),
(2, 2, '2025-01-15', 'Active');

INSERT INTO Sensors (ParcelID, SensorType)
VALUES
(1, 'SoilSensor-Pro'),
(2, 'AgroMonitor-X');

INSERT INTO Sensor_Readings 
(SensorID, ReadingTimestamp, SoilPH, Moisture, Temperature, Humidity, Rainfall)
VALUES
(1, '2025-02-10 08:00:00.123456', 6.40, 11.50, 21.00, 70.00, 0.00),
(1, '2025-02-10 12:00:00.123456', 6.45, 12.20, 22.50, 68.00, 0.00),
(2, '2025-02-10 09:00:00.123456', 5.95, 14.50, 27.50, 75.00, 2.00);

INSERT INTO Harvest_Submissions 
(CycleID, FarmerID, QuantityKg)
VALUES
(1, 1, 1500.00),
(2, 2, 2000.00);

INSERT INTO Aggregation_Lots (LotStatus)
VALUES ('Open');

INSERT INTO Lot_Contributions 
(LotID, HarvestID, ContributedQuantityKg, QualityScore)
VALUES
(1, 1, 1500.00, 92.50),
(1, 2, 2000.00, 95.00);

INSERT INTO Lot_Inspections 
(LotID, InspectorID, PhysicalResult, FinalDecision)
VALUES
(1, 3, 'Meets export moisture and quality standards', 'Approved');

INSERT INTO Export_Contracts
(BuyerID, LotID, ContractQuantityKg, PricePerKg, Status)
VALUES
(4, 1, 3500.00, 250.00, 'Active');

INSERT INTO Payments
(ContractID, TotalAmount)
VALUES
(1, 875000.00);

INSERT INTO Farmer_Payouts
(PaymentID, FarmerID, Amount)
VALUES
(1, 1, 375000.00),
(1, 2, 500000.00);

