import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- ACCESS GUARD ---
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("You must log in to access this page.")
    st.switch_page("app.py")

if st.session_state.role != "Inspector":
    st.error("Access Denied: You do not have permission to view the Inspector Dashboard.")
    st.stop()

API_BASE_URL = "http://localhost:8000"
INSPECTOR_ID = st.session_state.user_id

if "inspector_flash" in st.session_state:
    st.success(st.session_state.pop("inspector_flash"))


def fetch_json(url):
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def inspect_lot(lot_id, decision):
    try:
        response = requests.post(
            f"{API_BASE_URL}/inspection/inspect",
            json={
                "lot_id": int(lot_id),
                "inspector_id": INSPECTOR_ID,
                "decision": decision,
            }
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


st.set_page_config(layout="wide")
st.title("Inspector & Quality Assurance Dashboard")
st.caption(f"Logged in as Inspector ID: {INSPECTOR_ID}")

pending_payload = fetch_json(f"{API_BASE_URL}/inspection/pending-lots")
pending_lots = pending_payload.get("lots", []) if isinstance(pending_payload, dict) else []

if "error" in pending_payload:
    st.error(pending_payload["error"])
    st.stop()

if not pending_lots:
    st.warning("No pending lots for inspection.")
    st.stop()

lots_df = pd.DataFrame(pending_lots).rename(columns={
    "lotid": "LotID",
    "createddate": "CreatedDate",
    "totalweight": "TotalWeight"
})

st.sidebar.header("Filters")
search_id = st.sidebar.text_input("Search Lot ID")

filtered_df = lots_df.copy()
if search_id:
    filtered_df = filtered_df[filtered_df["LotID"].astype(str).str.contains(search_id)]

st.subheader("Pending Lots")
st.dataframe(filtered_df, width='stretch')

if filtered_df.empty:
    st.warning("No lots match the current filter.")
    st.stop()

selected_lot = st.selectbox("Select Lot for Inspection", filtered_df["LotID"])

contribution_payload = fetch_json(f"{API_BASE_URL}/lot/{selected_lot}/contributions")
trace_payload = fetch_json(f"{API_BASE_URL}/lot/{selected_lot}/trace")

st.markdown("---")
st.markdown(f"## Inspection Workspace: Lot {selected_lot}")

tab1, tab2, tab3 = st.tabs([
    "Contribution & Quality",
    "Traceability Snapshot",
    "Final Decision"
])

with tab1:
    st.subheader("Contribution Breakdown")

    contributions = contribution_payload.get("contributions", []) if isinstance(contribution_payload, dict) else []
    if contributions:
        contrib_df = pd.DataFrame(contributions).rename(columns={
            "contributionid": "Contribution ID",
            "harvestid": "Harvest ID",
            "contributedquantitykg": "Weight (kg)",
            "qualityscore": "Quality Score",
            "farmerid": "Farmer ID",
            "cycleid": "Cycle ID",
            "contribution_percent": "Contribution %"
        })
        st.dataframe(contrib_df, width='stretch')

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Weight", f"{float(contribution_payload['total_quantity']):.2f} kg")
        col2.metric("Farmer Count", contrib_df["Farmer ID"].nunique())
        avg_quality = contrib_df["Quality Score"].dropna().mean() if "Quality Score" in contrib_df else None
        col3.metric("Avg Quality Score", f"{avg_quality:.2f}" if pd.notna(avg_quality) else "N/A")
    else:
        st.info("No lot contributions found.")

    if isinstance(trace_payload, dict) and trace_payload.get("sensor_summary"):
        st.markdown("### Latest Sensor Summary")
        sensor_df = pd.DataFrame(trace_payload["sensor_summary"]).rename(columns={
            "sensorid": "Sensor ID",
            "parcelid": "Parcel ID",
            "moisture": "Moisture",
            "soilph": "Soil pH",
            "readingtimestamp": "Timestamp"
        })
        st.dataframe(sensor_df, width='stretch')

with tab2:
    st.subheader("Traceability Snapshot")

    if "error" in trace_payload:
        st.error(trace_payload["error"])
    else:
        timeline = trace_payload.get("timeline", [])
        if timeline:
            for event in timeline:
                st.write(f"{event['stage']} | {event['time']}")

        parcels = trace_payload.get("parcels", [])
        if parcels:
            st.markdown("### Parcels")
            st.dataframe(pd.DataFrame(parcels), width='stretch')

        farmers = trace_payload.get("farmers", [])
        if farmers:
            st.markdown("### Farmers")
            st.dataframe(pd.DataFrame(farmers), width='stretch')

with tab3:
    st.subheader("Inspection Decision")
    st.write("Submitting a decision will create a lot inspection row and update the lot status through the trigger.")

    decision = st.radio("Decision", ["Approved", "Rejected"], horizontal=True)

    if st.button("Submit Inspection Decision", use_container_width=True):
        result = inspect_lot(selected_lot, decision)
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state["inspector_flash"] = (
                f"{result['message']} | Updated Lot Status: {result.get('updated_status', 'Unknown')}"
            )
            st.rerun()

    report = f"""
Lot ID: {selected_lot}
Inspector ID: {INSPECTOR_ID}
Inspection Date: {datetime.now()}
Contribution Summary:
{contribution_payload}
"""
    st.download_button(
        label="Download Inspection Snapshot",
        data=report,
        file_name=f"inspection_{selected_lot}.txt"
    )
