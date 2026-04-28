CREATE OR REPLACE FUNCTION check_crop_risk()
RETURNS TRIGGER AS $$
DECLARE
    v_parcel_id INT;
    v_cycle_id INT;
    v_crop_id INT;
    v_ideal_ph DECIMAL(4,2);
    v_ideal_moisture DECIMAL(5,2);
BEGIN
    -- Step 1: Get ParcelID from Sensors
    SELECT ParcelID INTO v_parcel_id
    FROM Sensors
    WHERE SensorID = NEW.SensorID;

    IF v_parcel_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Step 2: Get ACTIVE crop cycle for this parcel
    SELECT CycleID, CropID
    INTO v_cycle_id, v_crop_id
    FROM Crop_Cycles
    WHERE ParcelID = v_parcel_id
      AND Status = 'Active'
    LIMIT 1;

    IF v_cycle_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Step 3: Get crop thresholds
    SELECT IdealSoilPH, IdealMoisture
    INTO v_ideal_ph, v_ideal_moisture
    FROM Crops
    WHERE CropID = v_crop_id;

    -- Step 4: Risk logic (simple deviation threshold)
    IF (
        NEW.SoilPH < v_ideal_ph - 1 OR
        NEW.SoilPH > v_ideal_ph + 1 OR
        NEW.Moisture < v_ideal_moisture - 10 OR
        NEW.Moisture > v_ideal_moisture + 10
    ) THEN

        -- Only update if still Active (avoid redundant writes)
        UPDATE Crop_Cycles
        SET Status = 'AtRisk'
        WHERE CycleID = v_cycle_id
          AND Status = 'Active';

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_crop_risk
AFTER INSERT ON Sensor_Readings
FOR EACH ROW
EXECUTE FUNCTION check_crop_risk();

CREATE OR REPLACE FUNCTION update_lot_status_after_inspection()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.FinalDecision = 'Approved' THEN
        UPDATE Aggregation_Lots
        SET LotStatus = 'Approved'
        WHERE LotID = NEW.LotID;

    ELSIF NEW.FinalDecision = 'Rejected' THEN
        UPDATE Aggregation_Lots
        SET LotStatus = 'Rejected'
        WHERE LotID = NEW.LotID;

    ELSIF NEW.FinalDecision = 'Reclassified' THEN
        UPDATE Aggregation_Lots
        SET LotStatus = 'Open'
        WHERE LotID = NEW.LotID;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_lot_status
AFTER INSERT ON Lot_Inspections
FOR EACH ROW
EXECUTE FUNCTION update_lot_status_after_inspection();