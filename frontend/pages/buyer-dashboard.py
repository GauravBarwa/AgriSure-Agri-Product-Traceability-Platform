import streamlit as st
import pandas as pd
import requests

# --- ACCESS GUARD ---
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("You must log in to access this page.")
    st.switch_page("app.py")

if st.session_state.role != "Buyer":
    st.error("Access Denied: You do not have permission to view the Buyer Dashboard.")
    st.stop()

API_BASE_URL = "http://localhost:8000"
BUYER_ID = st.session_state.user_id

if "buyer_flash" in st.session_state:
    st.success(st.session_state.pop("buyer_flash"))


def fetch_json(url):
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def create_contract(lot_id, qty, price):
    try:
        response = requests.post(
            f"{API_BASE_URL}/contract/create",
            json={
                "buyer_id": BUYER_ID,
                "lot_id": int(lot_id),
                "price_per_kg": price,
                "contract_quantity": qty,
            }
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


st.set_page_config(layout="wide")
st.title("Buyer Procurement Portal")
st.caption(f"Logged in as Buyer ID: {BUYER_ID}")

approved_payload = fetch_json(f"{API_BASE_URL}/lot/approved")
contracts_payload = fetch_json(f"{API_BASE_URL}/contract/buyer/{BUYER_ID}")

approved_lots = approved_payload.get("lots", []) if isinstance(approved_payload, dict) else []
contracts = contracts_payload.get("contracts", []) if isinstance(contracts_payload, dict) else []

tab1, tab2, tab3 = st.tabs([
    "Available Lots",
    "Active Contracts",
    "Provenance & History"
])

with tab1:
    st.subheader("Approved Lots Available For Purchase")

    if "error" in approved_payload:
        st.error(approved_payload["error"])
    elif not approved_lots:
        st.info("No approved lots are currently available.")
    else:
        lots_df = pd.DataFrame(approved_lots).rename(columns={
            "lotid": "Lot ID",
            "lotstatus": "Status",
            "createddate": "Created Date",
            "totalweight": "Weight (kg)",
            "farmercount": "Farmer Count"
        })
        st.dataframe(lots_df, width='stretch')

        selected_lot = st.selectbox("Select Lot", lots_df["Lot ID"])
        selected_row = lots_df[lots_df["Lot ID"] == selected_lot].iloc[0]
        selected_weight = float(selected_row["Weight (kg)"]) if pd.notna(selected_row["Weight (kg)"]) else 0.0

        st.markdown("### Purchase Proposal")
        if selected_weight <= 0:
            st.warning("This lot has no valid contributed weight, so it cannot be purchased.")
        else:
            with st.form("buyer_contract_form"):
                price = st.number_input("Price Per Kg", min_value=1.0, value=250.0, step=10.0)
                qty = st.number_input(
                    "Contract Quantity (kg)",
                    min_value=1.0,
                    value=max(1.0, selected_weight),
                    step=100.0
                )
                submit = st.form_submit_button("Create Contract", use_container_width=True)

                if submit:
                    result = create_contract(selected_lot, qty, price)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["buyer_flash"] = (
                            f"Contract created successfully. Contract ID: {result['contract_id']}"
                        )
                        st.rerun()

with tab2:
    st.subheader("My Contracts")

    if "error" in contracts_payload:
        st.error(contracts_payload["error"])
    elif not contracts:
        st.info("No contracts found for this buyer.")
    else:
        contracts_df = pd.DataFrame(contracts).rename(columns={
            "contractid": "Contract ID",
            "lotid": "Lot ID",
            "contractquantitykg": "Quantity (kg)",
            "priceperkg": "Price Per Kg",
            "status": "Contract Status",
            "lotstatus": "Lot Status",
            "createddate": "Lot Created"
        })
        st.dataframe(contracts_df, width='stretch')

with tab3:
    st.subheader("Lot Provenance")

    lot_options = [contract["lotid"] for contract in contracts] if contracts else [lot["lotid"] for lot in approved_lots]

    if not lot_options:
        st.info("No lots available to trace yet.")
    else:
        trace_lot_id = st.selectbox("Select Lot For Traceability", lot_options)
        trace_payload = fetch_json(f"{API_BASE_URL}/lot/{trace_lot_id}/trace")

        if "error" in trace_payload:
            st.error(trace_payload["error"])
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Lot ID", trace_payload["lot_id"])
            col2.metric("Lot Status", trace_payload["lot_status"])
            col3.metric("Total Quantity", f"{float(trace_payload['total_quantity']):.2f} kg")

            if trace_payload.get("contributions"):
                st.markdown("### Farmer Contributions")
                st.dataframe(pd.DataFrame(trace_payload["contributions"]), width='stretch')

            if trace_payload.get("parcels"):
                st.markdown("### Source Parcels")
                st.dataframe(pd.DataFrame(trace_payload["parcels"]), width='stretch')

            if trace_payload.get("timeline"):
                st.markdown("### Lifecycle Timeline")
                st.dataframe(pd.DataFrame(trace_payload["timeline"]), width='stretch')
