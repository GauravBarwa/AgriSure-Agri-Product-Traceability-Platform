import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- ACCESS GUARD ---
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("You must log in to access this page.")
    st.switch_page("app.py")

if st.session_state.role != "Farmer":
    st.error("Access Denied: You do not have permission to view the Farmer Dashboard.")
    st.stop()

API_BASE_URL = "http://localhost:8000"
FARMER_ID = st.session_state.user_id

if "farmer_flash" in st.session_state:
    st.success(st.session_state.pop("farmer_flash"))


def parse_coordinate(value):
    value = value.strip()
    if value.endswith("N") or value.endswith("E"):
        return float(value[:-1])
    if value.endswith("S") or value.endswith("W"):
        return -float(value[:-1])
    return float(value)


def fetch_json(url, params=None):
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_parcels():
    return fetch_json(f"{API_BASE_URL}/farmer/parcels/{FARMER_ID}")


def fetch_sensor_status():
    return fetch_json(f"{API_BASE_URL}/farmer/sensor-status/{FARMER_ID}")


def fetch_crop_cycles():
    return fetch_json(f"{API_BASE_URL}/farmer/crop-cycles/{FARMER_ID}")


def submit_harvest(cycle_id, quantity):
    try:
        response = requests.post(
            f"{API_BASE_URL}/farmer/harvest",
            params={
                "cycle_id": cycle_id,
                "farmer_id": FARMER_ID,
                "quantity": quantity,
            },
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


st.title("Farmer Dashboard")
st.write(f"Welcome, Farmer ID: {FARMER_ID}")

section = st.sidebar.radio(
    "Go to",
    ["My Parcels", "Sensor Insights", "Harvest Submission"]
)

parcels_payload = fetch_parcels()
cycles_payload = fetch_crop_cycles()
sensor_payload = fetch_sensor_status()

parcels = parcels_payload.get("parcels", []) if isinstance(parcels_payload, dict) else []
cycles = cycles_payload.get("cycles", []) if isinstance(cycles_payload, dict) else []
sensors = sensor_payload.get("sensor_summary", []) if isinstance(sensor_payload, dict) else []

if section == "My Parcels":
    st.markdown("## My Parcels")

    if "error" in parcels_payload:
        st.error(parcels_payload["error"])
        st.stop()

    if not parcels:
        st.info("No parcels found for this farmer yet.")
        st.stop()

    parcel_df = pd.DataFrame(parcels)
    display_df = parcel_df.rename(columns={
        "parcelid": "Parcel ID",
        "locationcoordinates": "Coordinates",
        "areahectares": "Area (ha)",
        "elevationmsl": "Elevation MSL",
        "certificationstatus": "Certification"
    })
    st.dataframe(display_df, width='stretch')

    coords = parcel_df["locationcoordinates"].str.split(",", expand=True)
    map_df = pd.DataFrame({
        "lat": coords[0].apply(parse_coordinate),
        "lon": coords[1].apply(parse_coordinate),
    })
    st.map(map_df)

elif section == "Sensor Insights":
    st.markdown("## Sensor Status & Risk Assessment")

    if "error" in sensor_payload:
        st.error(sensor_payload["error"])
        st.stop()

    if not sensors:
        st.info("No sensor data available for this farmer.")
        st.stop()

    sensor_df = pd.DataFrame(sensors)
    sensor_df.rename(columns={
        "parcelid": "Parcel ID",
        "sensorid": "Sensor ID",
        "moisture": "Moisture",
        "soilph": "Soil pH",
        "readingtimestamp": "Timestamp",
        "status": "Status"
    }, inplace=True)

    st.dataframe(sensor_df, width='stretch')

    for _, row in sensor_df.iterrows():
        st.markdown(f"### Parcel {row['Parcel ID']} | Sensor {row['Sensor ID']}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Moisture", f"{float(row['Moisture']):.2f}%")
        col2.metric("Soil pH", f"{float(row['Soil pH']):.2f}")
        col3.metric("Status", row["Status"])

        if row["Status"] == "Low Moisture":
            st.error("Immediate irrigation required.")
        elif row["Status"] == "High Moisture":
            st.warning("Moisture is above the healthy range.")
        else:
            st.success("Latest reading is within the healthy range.")
        st.caption(f"Last updated: {row['Timestamp']}")
        st.divider()

elif section == "Harvest Submission":
    st.markdown("## Submit Harvest")

    if "error" in cycles_payload:
        st.error(cycles_payload["error"])
        st.stop()

    if not cycles:
        st.info("No crop cycles available for harvest submission.")
        st.stop()

    cycle_df = pd.DataFrame(cycles)
    cycle_df.rename(columns={
        "cycleid": "Cycle ID",
        "cropname": "Crop",
        "status": "Status",
        "startdate": "Start Date",
        "enddate": "End Date",
        "parcelid": "Parcel ID"
    }, inplace=True)

    st.dataframe(cycle_df, width='stretch')

    cycle_options = {
        f"Cycle {row['Cycle ID']} | Parcel {row['Parcel ID']} | {row['Crop']} | {row['Status']}": row["Cycle ID"]
        for _, row in cycle_df.iterrows()
        if row["Status"] == "Active"
    }

    if not cycle_options:
        st.info("There are no active crop cycles available for harvest submission.")
        st.stop()

    with st.form("harvest_form"):
        selected_cycle_label = st.selectbox("Select Active Crop Cycle", list(cycle_options.keys()))
        quantity = st.number_input("Harvest Quantity (kg)", min_value=1.0, step=10.0)
        harvest_date = st.date_input("Harvest Date", datetime.today())
        submitted = st.form_submit_button("Submit Harvest", use_container_width=True)

        if submitted:
            result = submit_harvest(cycle_options[selected_cycle_label], quantity)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["farmer_flash"] = (
                    f"Harvest submitted successfully. Harvest ID: {result['harvest_id']} | "
                    f"Recorded Date: {harvest_date}"
                )
                st.rerun()
