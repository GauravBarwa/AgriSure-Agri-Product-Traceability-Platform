-- create db

CREATE DATABASE agrisure;
\c agrisure;

-- user roles

CREATE TABLE User_Accounts (
    UserID SERIAL PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash TEXT NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    RoleType VARCHAR(20) NOT NULL CHECK (
        RoleType IN ('Farmer', 'Inspector', 'Buyer', 'Admin')
    ),
    AccountStatus VARCHAR(20) DEFAULT 'Active'
);

-- Farmers, Quality Inspectors, Buyers, Admins

CREATE TABLE Farmers (
    UserID INT PRIMARY KEY,
    RegistrationDate DATE NOT NULL,
    FarmerStatus VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (UserID) REFERENCES User_Accounts(UserID) ON DELETE CASCADE
);

CREATE TABLE Quality_Inspectors (
    UserID INT PRIMARY KEY,
    CertificationLevel VARCHAR(50) NOT NULL,
    Organization VARCHAR(100),
    FOREIGN KEY (UserID) REFERENCES User_Accounts(UserID) ON DELETE CASCADE
);

CREATE TABLE Export_Buyers (
    UserID INT PRIMARY KEY,
    CompanyName VARCHAR(100) NOT NULL,
    Country VARCHAR(100) NOT NULL,
    ContactInfo TEXT,
    FOREIGN KEY (UserID) REFERENCES User_Accounts(UserID) ON DELETE CASCADE
);

CREATE TABLE Coop_Admins (
    UserID INT PRIMARY KEY,
    AdminLevel INT CHECK (AdminLevel >= 1),
    FOREIGN KEY (UserID) REFERENCES User_Accounts(UserID) ON DELETE CASCADE
);

CREATE TABLE Crops (
    CropID SERIAL PRIMARY KEY,
    CropName VARCHAR(100) NOT NULL,
    Variety VARCHAR(100) UNIQUE NOT NULL,
    IdealSoilPH DECIMAL(4,2) CHECK (IdealSoilPH BETWEEN 0 AND 14),
    IdealMoisture DECIMAL(5,2) CHECK (IdealMoisture >= 0),
    IdealTemperature DECIMAL(5,2)
);

CREATE TABLE Land_Parcels (
    ParcelID SERIAL PRIMARY KEY,
    FarmerID INT NOT NULL,
    LocationCoordinates TEXT NOT NULL,
    AreaHectares DECIMAL(6,2) CHECK (AreaHectares > 0),
    ElevationMSL DECIMAL(8,2),
    SoilBaselineJSON JSONB,
    CertificationStatus VARCHAR(50),
    FOREIGN KEY (FarmerID) REFERENCES Farmers(UserID) ON DELETE RESTRICT
);

CREATE TABLE Crop_Cycles (
    CycleID SERIAL PRIMARY KEY,
    ParcelID INT NOT NULL,
    CropID INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE,
    Status VARCHAR(20) DEFAULT 'Active' CHECK (
        Status IN ('Active', 'AtRisk', 'Completed')
    ),
    FOREIGN KEY (ParcelID) REFERENCES Land_Parcels(ParcelID) ON DELETE RESTRICT,
    FOREIGN KEY (CropID) REFERENCES Crops(CropID) ON DELETE RESTRICT
);

CREATE TABLE Sensors (
    SensorID SERIAL PRIMARY KEY,
    ParcelID INT NOT NULL,
    SensorType VARCHAR(50),
    Status VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (ParcelID) REFERENCES Land_Parcels(ParcelID) ON DELETE CASCADE
);

--Sensor readings, weak entity

CREATE TABLE Sensor_Readings (
    SensorID INT,
    ReadingTimestamp TIMESTAMP(6),
    SoilPH DECIMAL(4,2) NOT NULL,
    Moisture DECIMAL(5,2) NOT NULL,
    Temperature DECIMAL(5,2),
    Humidity DECIMAL(5,2),
    Rainfall DECIMAL(5,2),
    PRIMARY KEY (SensorID, ReadingTimestamp),
    FOREIGN KEY (SensorID) REFERENCES Sensors(SensorID) ON DELETE CASCADE
);

CREATE TABLE Harvest_Submissions (
    HarvestID SERIAL PRIMARY KEY,
    CycleID INT NOT NULL,
    FarmerID INT NOT NULL,
    QuantityKg DECIMAL(10,2) CHECK (QuantityKg > 0),
    SubmissionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (CycleID) REFERENCES Crop_Cycles(CycleID),
    FOREIGN KEY (FarmerID) REFERENCES Farmers(UserID)
);

CREATE TABLE Aggregation_Lots (
    LotID SERIAL PRIMARY KEY,
    LotStatus VARCHAR(20) DEFAULT 'Open' CHECK (
        LotStatus IN ('Open', 'Locked', 'Approved', 'Rejected')
    ),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- lot contribution

CREATE TABLE Lot_Contributions (
    ContributionID SERIAL PRIMARY KEY,
    LotID INT NOT NULL,
    HarvestID INT NOT NULL,
    ContributedQuantityKg DECIMAL(10,2) CHECK (ContributedQuantityKg > 0),
    QualityScore DECIMAL(5,2),
    FOREIGN KEY (LotID) REFERENCES Aggregation_Lots(LotID) ON DELETE CASCADE,
    FOREIGN KEY (HarvestID) REFERENCES Harvest_Submissions(HarvestID)
);

CREATE TABLE Lot_Inspections (
    InspectionID SERIAL PRIMARY KEY,
    LotID INT NOT NULL,
    InspectorID INT NOT NULL,
    InspectionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PhysicalResult TEXT,
    FinalDecision VARCHAR(20) CHECK (
        FinalDecision IN ('Approved', 'Reclassified', 'Rejected')
    ),
    FOREIGN KEY (LotID) REFERENCES Aggregation_Lots(LotID),
    FOREIGN KEY (InspectorID) REFERENCES Quality_Inspectors(UserID)
);

--export contracts

CREATE TABLE Export_Contracts (
    ContractID SERIAL PRIMARY KEY,
    BuyerID INT NOT NULL,
    LotID INT UNIQUE NOT NULL,
    ContractQuantityKg DECIMAL(10,2) CHECK (ContractQuantityKg > 0),
    PricePerKg DECIMAL(10,2) CHECK (PricePerKg > 0),
    Status VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (BuyerID) REFERENCES Export_Buyers(UserID),
    FOREIGN KEY (LotID) REFERENCES Aggregation_Lots(LotID)
);

CREATE TABLE Payments (
    PaymentID SERIAL PRIMARY KEY,
    ContractID INT NOT NULL,
    TotalAmount DECIMAL(12,2) CHECK (TotalAmount > 0),
    PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ContractID) REFERENCES Export_Contracts(ContractID)
);

CREATE TABLE Farmer_Payouts (
    PayoutID SERIAL PRIMARY KEY,
    PaymentID INT NOT NULL,
    FarmerID INT NOT NULL,
    Amount DECIMAL(10,2) CHECK (Amount > 0),
    CalculationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PaymentID) REFERENCES Payments(PaymentID) ON DELETE CASCADE,
    FOREIGN KEY (FarmerID) REFERENCES Farmers(UserID)
);

CREATE TABLE Contract_Payout_Config (
    ConfigID SERIAL PRIMARY KEY,
    ContractID INT UNIQUE,
    
    WeightQuantity DECIMAL(5,2) DEFAULT 1.0,
    WeightQuality DECIMAL(5,2) DEFAULT 0.0,
    
    BonusThreshold DECIMAL(5,2),   -- optional
    BonusMultiplier DECIMAL(5,2),  -- optional
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ContractID) REFERENCES Export_Contracts(ContractID)
);

-- Indexing

CREATE INDEX idx_crop_cycle_parcel ON Crop_Cycles(ParcelID);
CREATE INDEX idx_sensor_reading_time ON Sensor_Readings(ReadingTimestamp);
CREATE INDEX idx_sensor_parcel ON Sensors(ParcelID);
CREATE INDEX idx_contract_lot ON Export_Contracts(LotID);
CREATE INDEX idx_payment_contract ON Payments(ContractID);
CREATE INDEX idx_harvest_cycle ON Harvest_Submissions(CycleID);

