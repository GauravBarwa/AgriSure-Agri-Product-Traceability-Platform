import json

import pandas as pd
import requests
import streamlit as st

# --- ACCESS GUARD ---
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("You must log in to access this page.")
    st.switch_page("app.py")

if st.session_state.role != "Admin":
    st.error("Access Denied: You do not have permission to view the Admin Dashboard.")
    st.stop()

API_BASE_URL = "http://localhost:8000"

if "admin_flash" in st.session_state:
    st.success(st.session_state.pop("admin_flash"))


def get_json(path):
    try:
        response = requests.get(f"{API_BASE_URL}{path}")
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def post_json(path, payload=None, params=None):
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def add_farmer_api(username, email, password):
    return post_json(
        "/admin/addfarmer",
        params={
            "username": username,
            "email": email,
            "passwordHash": password,
        },
    )


def add_parcel_api(payload):
    return post_json("/farmer/add-parcel", payload=payload)


def create_lot_api(harvest_ids):
    return post_json("/lot/create", payload={"harvest_ids": harvest_ids})


def fetch_farmers():
    return get_json("/farmer/all_farmers")


def fetch_available_harvests():
    return get_json("/lot/available-harvests")


def fetch_all_contracts():
    return get_json("/contract/all")


def fetch_task6_participants():
    return get_json("/transaction-demo/participants")


def run_double_sale_demo(payload):
    return post_json("/transaction-demo/double-sale", payload=payload)


def run_double_inspection_demo(payload):
    return post_json("/transaction-demo/double-inspection", payload=payload)


def render_task6_result(data, record_key):
    if "error" in data:
        st.error(data["error"])
        return

    summary = data.get("summary", {})
    result_rows = [{"actor_key": key, **value} for key, value in data.get("results", {}).items()]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Demo Lot ID", data.get("lot_id", "-"))
    col2.metric("Transactions Started", summary.get("transactions_started", 0))
    col3.metric("Committed", summary.get("transactions_committed", 0))
    col4.metric("Rolled Back", summary.get("transactions_rolled_back", 0))

    if summary.get("expected_outcome"):
        st.info(summary["expected_outcome"])

    if result_rows:
        st.markdown("### Actor Outcomes")
        st.dataframe(pd.DataFrame(result_rows), width='stretch')

    records = data.get(record_key, [])
    if records:
        title = "Contracts Created" if record_key == "contracts" else "Inspections Created"
        st.markdown(f"### {title}")
        st.dataframe(pd.DataFrame(records), width='stretch')

    if data.get("final_lot"):
        st.markdown("### Final Lot State")
        st.dataframe(pd.DataFrame([data["final_lot"]]), width='stretch')

    if data.get("logs"):
        st.markdown("### Transaction Timeline")
        st.dataframe(pd.DataFrame(data["logs"]), width='stretch')


st.set_page_config(layout="wide")
st.title("Cooperative Admin Dashboard")
st.caption("Admin control panel for stakeholder onboarding, lot orchestration, transaction demos, and payout execution.")

section = st.sidebar.radio(
    "Navigate",
    ["Onboarding", "Inventory", "Transactions", "Finance"]
)

if section == "Onboarding":
    st.markdown("## Stakeholder Onboarding")

    farmers_payload = fetch_farmers()
    farmers = farmers_payload if isinstance(farmers_payload, list) else []

    tab1, tab2 = st.tabs(["Farmer Registration", "Parcel Registry"])

    with tab1:
        st.subheader("Register New Farmer")
        with st.form("register_farmer_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_farmer = st.form_submit_button("Register Farmer", use_container_width=True)

            if submit_farmer:
                result = add_farmer_api(username, email, password)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["admin_flash"] = (
                        f"Farmer registered successfully. User ID: {result['user_id']} | "
                        f"Farmer ID: {result['farmer_id']}"
                    )
                    st.rerun()

        st.markdown("### Existing Farmers")
        if farmers:
            st.dataframe(pd.DataFrame(farmers), width='stretch')
        else:
            st.info("No farmers found.")

    with tab2:
        st.subheader("Register Land Parcel")

        farmer_options = {
            f"{farmer['username']} ({farmer['email']})": farmer["userid"]
            for farmer in farmers
        }

        with st.form("add_parcel_form"):
            farmer_label = st.selectbox("Select Farmer", list(farmer_options.keys())) if farmer_options else None
            location = st.text_input("Location Coordinates", value="12.9716N,77.5946E")
            area = st.number_input("Area (hectares)", min_value=0.1, value=2.5, step=0.1)
            elevation = st.number_input("Elevation MSL", min_value=0.0, value=920.0, step=10.0)
            certification = st.text_input("Certification Status", value="Organic")
            soil_json = st.text_area(
                "Soil Baseline JSON",
                value='{"nitrogen":"medium","organic_matter":"high"}'
            )
            submit_parcel = st.form_submit_button("Add Parcel", use_container_width=True)

            if submit_parcel:
                if not farmer_label:
                    st.error("No farmers available to assign the parcel.")
                else:
                    try:
                        payload = {
                            "farmer_id": farmer_options[farmer_label],
                            "location_coordinates": location,
                            "area_hectares": area,
                            "elevation_msl": elevation,
                            "soil_baseline_json": json.loads(soil_json),
                            "certification_status": certification,
                        }
                    except json.JSONDecodeError:
                        payload = None
                        st.error("Soil baseline must be valid JSON.")

                    if payload:
                        result = add_parcel_api(payload)
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.session_state["admin_flash"] = (
                                f"Parcel added successfully. Parcel ID: {result['parcel_id']}"
                            )
                            st.rerun()

elif section == "Inventory":
    st.markdown("## Lot Orchestration")

    harvests_payload = fetch_available_harvests()
    harvests = harvests_payload.get("harvests", []) if isinstance(harvests_payload, dict) else []

    if "error" in harvests_payload:
        st.error(harvests_payload["error"])
    elif not harvests:
        st.info("No unassigned harvest submissions are available for lot creation.")
    else:
        harvest_df = pd.DataFrame(harvests).rename(columns={
            "harvestid": "Harvest ID",
            "farmerid": "Farmer ID",
            "cycleid": "Cycle ID",
            "quantitykg": "Quantity (kg)",
            "submissiondate": "Submission Date",
            "cropname": "Crop"
        })
        st.dataframe(harvest_df, width='stretch')

        options = {
            f"Harvest {row['Harvest ID']} | Farmer {row['Farmer ID']} | {row['Crop']} | {float(row['Quantity (kg)']):.2f} kg": row["Harvest ID"]
            for _, row in harvest_df.iterrows()
        }

        selected_labels = st.multiselect("Select Harvests For New Aggregation Lot", list(options.keys()))

        if st.button("Create Aggregation Lot", use_container_width=True):
            if not selected_labels:
                st.warning("Select at least one harvest.")
            else:
                harvest_ids = [options[label] for label in selected_labels]
                result = create_lot_api(harvest_ids)

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["admin_flash"] = (
                        f"Aggregation lot created successfully. Lot ID: {result['lot_id']} | "
                        f"Total Quantity: {float(result['total_quantity']):.2f} kg"
                    )
                    st.rerun()

        st.caption("Once a lot is created, the inspector should approve or reject it from the Inspector dashboard.")

elif section == "Transactions":
    st.markdown("## Task 6 Transaction Demo Lab")
    st.caption("Run conflicting PostgreSQL transactions and inspect the resulting database state.")

    participants = fetch_task6_participants()
    if "error" in participants:
        st.error(participants["error"])
        st.stop()

    meta1, meta2, meta3, meta4 = st.columns(4)
    meta1.metric("Buyer A", participants.get("buyer_a_id", "-"))
    meta2.metric("Buyer B", participants.get("buyer_b_id", "-"))
    meta3.metric("Inspector A", participants.get("inspector_a_id", "-"))
    meta4.metric("Inspector B", participants.get("inspector_b_id", "-"))

    tab1, tab2 = st.tabs(["Scenario A: Double Sale", "Scenario B: Duplicate Inspection"])

    with tab1:
        with st.form("task6_sale_form"):
            col1, col2 = st.columns(2)
            with col1:
                quantity = st.number_input("Contract Quantity (kg)", min_value=1.0, value=1200.0, step=100.0)
                buyer_a_hold = st.slider("Buyer A Lock Hold (s)", 0.0, 5.0, 2.0, 0.5)
            with col2:
                price = st.number_input("Price Per Kg", min_value=1.0, value=250.0, step=10.0)
                buyer_b_hold = st.slider("Buyer B Lock Hold (s)", 0.0, 5.0, 0.0, 0.5)
                isolation = st.selectbox("Isolation Level", ["SERIALIZABLE", "REPEATABLE READ", "READ COMMITTED"])
            run_sale = st.form_submit_button("Run Double-Sale Demo", use_container_width=True)

        if run_sale:
            st.session_state["task6_sale_result"] = run_double_sale_demo({
                "contract_quantity": quantity,
                "price_per_kg": price,
                "buyer_a_hold_seconds": buyer_a_hold,
                "buyer_b_hold_seconds": buyer_b_hold,
                "isolation_level": isolation
            })

        if "task6_sale_result" in st.session_state:
            render_task6_result(st.session_state["task6_sale_result"], "contracts")

    with tab2:
        with st.form("task6_inspection_form"):
            col1, col2 = st.columns(2)
            with col1:
                inspector_a_decision = st.selectbox("Inspector A Decision", ["Approved", "Rejected"])
                inspector_a_hold = st.slider("Inspector A Lock Hold (s)", 0.0, 5.0, 2.0, 0.5)
            with col2:
                inspector_b_decision = st.selectbox("Inspector B Decision", ["Rejected", "Approved"])
                inspector_b_hold = st.slider("Inspector B Lock Hold (s)", 0.0, 5.0, 0.0, 0.5)
                isolation = st.selectbox(
                    "Isolation Level",
                    ["SERIALIZABLE", "REPEATABLE READ", "READ COMMITTED"],
                    key="task6_inspection_iso"
                )
            run_inspection = st.form_submit_button("Run Double-Inspection Demo", use_container_width=True)

        if run_inspection:
            st.session_state["task6_inspection_result"] = run_double_inspection_demo({
                "inspector_a_decision": inspector_a_decision,
                "inspector_b_decision": inspector_b_decision,
                "inspector_a_hold_seconds": inspector_a_hold,
                "inspector_b_hold_seconds": inspector_b_hold,
                "isolation_level": isolation
            })

        if "task6_inspection_result" in st.session_state:
            render_task6_result(st.session_state["task6_inspection_result"], "inspections")

elif section == "Finance":
    st.markdown("## Payments & Payouts")

    contracts_payload = fetch_all_contracts()
    contracts = contracts_payload.get("contracts", []) if isinstance(contracts_payload, dict) else []

    if "error" in contracts_payload:
        st.error(contracts_payload["error"])
        st.stop()

    if contracts:
        contracts_df = pd.DataFrame(contracts).rename(columns={
            "contractid": "Contract ID",
            "buyerid": "Buyer ID",
            "lotid": "Lot ID",
            "contractquantitykg": "Quantity (kg)",
            "priceperkg": "Price Per Kg",
            "status": "Contract Status",
            "lotstatus": "Lot Status"
        })
        st.dataframe(contracts_df, width='stretch')
        contract_id = st.selectbox("Select Contract", contracts_df["Contract ID"])
    else:
        st.info("No contracts available yet.")
        st.stop()

    st.markdown("### Payout Configuration")
    col1, col2 = st.columns(2)
    weight_quantity = col1.number_input("Weight Quantity", value=1.0)
    weight_quality = col2.number_input("Weight Quality", value=0.0)
    col3, col4 = st.columns(2)
    bonus_threshold = col3.number_input("Bonus Threshold", value=0.0)
    bonus_multiplier = col4.number_input("Bonus Multiplier", value=1.0)

    if st.button("Save Payout Configuration", use_container_width=True):
        result = post_json(
            f"/contract/{contract_id}/config",
            payload={
                "weight_quantity": weight_quantity,
                "weight_quality": weight_quality,
                "bonus_threshold": bonus_threshold,
                "bonus_multiplier": bonus_multiplier
            }
        )
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state["admin_flash"] = "Payout configuration saved."
            st.rerun()

    st.markdown("### Execute Payment")
    if st.button("Create Payment & Distribute Payouts", use_container_width=True):
        result = post_json("/payment/create", payload={"contract_id": int(contract_id)})
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Payment executed successfully.")
            st.write(f"Payment ID: {result['payment_id']}")
            st.write(f"Total Amount: {float(result['total_amount']):.2f}")
            st.dataframe(pd.DataFrame(result["payouts"]), width='stretch')

    st.markdown("### Payment History")
    if st.button("Fetch Payout History", use_container_width=True):
        history = get_json(f"/payment/{contract_id}/payouts")
        if "error" in history:
            st.error(history["error"])
        elif not history.get("payouts"):
            st.info("No payouts found for this contract yet.")
        else:
            st.dataframe(pd.DataFrame(history["payouts"]), width='stretch')
