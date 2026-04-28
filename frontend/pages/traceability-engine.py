import streamlit as st
import pandas as pd
import requests

st.set_page_config(layout="wide")

st.title("AgriSure Traceability Dashboard")

# ---------------------------------------
# INPUT
# ---------------------------------------
st.sidebar.header("Trace Input")

lot_id = st.sidebar.number_input("Enter Lot ID", min_value=1, step=1)
trace_button = st.sidebar.button("Trace Lot")

# ---------------------------------------
# MAIN
# ---------------------------------------
if trace_button:

    with st.spinner("Fetching traceability data..."):

        try:
            response = requests.get(
                f"http://localhost:8000/lot/{lot_id}/trace"
            )
            data = response.json()

        except:
            st.error("Could not connect to backend")
            st.stop()

    if "error" in data:
        st.error(data["error"])
        st.stop()

    # ---------------------------------------
    # OVERVIEW
    # ---------------------------------------
    st.subheader("Lot Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Lot ID", data["lot_id"])
    col2.metric("Lot Status", data["lot_status"])
    col3.metric("Total Quantity (kg)", round(data["total_quantity"], 2))

    st.divider()

    # ---------------------------------------
    # TIMELINE 
    # ---------------------------------------
    st.subheader("Lifecycle Timeline")

    timeline = data["timeline"]

    for i, event in enumerate(timeline):

        if "Approved" in event["stage"]:
            st.success(event["stage"])
        elif "Rejected" in event["stage"]:
            st.error(event["stage"])

        # choose icon based on stage
        if "Harvest" in event["stage"]:
            icon = "Harvest"
        elif "Lot" in event["stage"]:
            icon = "Lot"
        elif "Inspection" in event["stage"]:
            icon = "Inspection"
        elif "Payment" in event["stage"]:
            icon = "Payment"
        else:
            icon = "•"

        col1, col2 = st.columns([1, 10])

        with col1:
            st.markdown(f"### {icon}")

        with col2:
            st.markdown(f"**{event['stage']}**")
            st.caption(f"{event['time']}")

        # draw connector line (except last)
        if i < len(timeline) - 1:
            st.markdown(
                "<div style='margin-left:20px; border-left:2px solid #ccc; height:30px;'></div>",
                unsafe_allow_html=True
            )

    # ---------------------------------------
    # CONTRIBUTIONS
    # ---------------------------------------
    st.subheader("Farmer Contributions")

    contrib_df = pd.DataFrame(data["contributions"])

    if not contrib_df.empty:
        st.dataframe(contrib_df, width='stretch')

        st.subheader("Contribution % Distribution")
        chart = contrib_df.set_index("farmer_id")["contribution_percent"]
        st.bar_chart(chart)

    else:
        st.warning("No contributions found")

    st.divider()

    # ---------------------------------------
    # FARMERS SUMMARY
    # ---------------------------------------
    st.subheader("Farmers Summary")

    farmers_df = pd.DataFrame(data["farmers"])
    st.dataframe(farmers_df, width='stretch')

    st.divider()

    # ---------------------------------------
    # PARCEL MAP
    # ---------------------------------------
    st.subheader("Farm Locations")

    parcel_df = pd.DataFrame(data["parcels"])

    if not parcel_df.empty:

        # Split coordinates
        coords = parcel_df["location"].str.split(",", expand=True)

        def parse_coord(value):
            value = value.strip()

            if value.endswith("N"):
                return float(value[:-1])
            elif value.endswith("S"):
                return -float(value[:-1])
            elif value.endswith("E"):
                return float(value[:-1])
            elif value.endswith("W"):
                return -float(value[:-1])
            else:
                return float(value)

        parcel_df["lat"] = coords[0].apply(parse_coord)
        parcel_df["lon"] = coords[1].apply(parse_coord)

        st.map(parcel_df[["lat", "lon"]])

    else:
        st.warning("No parcel location data available")

    # ---------------------------------------
    # PARCEL INFO
    # ---------------------------------------
    st.subheader("Parcel Information")

    parcel_df = pd.DataFrame(data["parcels"])
    st.dataframe(parcel_df, width='stretch')

    st.divider()

    # ---------------------------------------
    # SENSOR DATA
    # ---------------------------------------
    st.subheader("Sensor Summary")

    sensor_df = pd.DataFrame(data["sensor_summary"])

    if not sensor_df.empty:
        st.dataframe(sensor_df, width='stretch')

        col1, col2 = st.columns(2)

        col1.metric("Avg Moisture", round(sensor_df["moisture"].mean(), 2))
        col2.metric("Avg Soil pH", round(sensor_df["soilph"].mean(), 2))

    else:
        st.warning("No sensor data available")

    st.divider()

    # ---------------------------------------
    # RAW DEBUG
    # ---------------------------------------
    with st.expander("Full Raw Data"):
        st.json(data)

else:
    st.info("Enter a Lot ID in the sidebar and click 'Trace Lot'")
