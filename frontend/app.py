import streamlit as st
import sys
import os

# This forces Python to look at the root 'AgriSure' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# NOW you can import the backend safely
from backend.db import execute_query 

st.set_page_config(page_title="AgriSure Login", layout="centered")

# --- 1. Initialize Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.username = None

# --- 2. Database Authentication Function ---
def authenticate_user(username, password):
    query = "SELECT UserID, RoleType, PasswordHash FROM User_Accounts WHERE Username = %s"
    try:
        # fetch=True returns a list of dictionaries based on your dict_row factory
        result = execute_query(query, (username,), fetch=True)
        
        if result and len(result) > 0:
            user = result[0]
            # Dictionary keys from psycopg dictate lowercase by default unless quoted in SQL
            db_password = user.get('passwordhash') or user.get('PasswordHash')
            db_role = user.get('roletype') or user.get('RoleType')
            db_userid = user.get('userid') or user.get('UserID')

            # NOTE: For Task 3, your DB has plain strings like 'hash1'. 
            # In a production app, you would use bcrypt.checkpw(password, db_password) here.
            if password == db_password:
                return {"user_id": db_userid, "role": db_role, "username": username}
    except Exception as e:
        st.error(f"Database connection error: {e}")
    
    return None

# --- 3. UI Layout ---
st.title("AgriSure System")

# If the user is already logged in, show them a welcome screen and routing options
if st.session_state.authenticated:
    st.success(f"Welcome back, {st.session_state.username}! (Role: {st.session_state.role})")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Enter Dashboard", use_container_width=True):
            # Map the database roles to the specific frontend pages
            role_page_map = {
                "Farmer": "pages/farmer-dashboard.py",
                "Inspector": "pages/inspector-dashboard.py",
                "Admin": "pages/admin-dashboard.py",
                "Buyer": "pages/buyer-dashboard.py"
            }
            if st.session_state.role in role_page_map:
                st.switch_page(role_page_map[st.session_state.role])
            else:
                st.error("Dashboard not configured for this role.")
                
    with col2:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# If not logged in, show the login form
else:
    st.markdown("### Login")
    with st.form("login_form"):
        input_username = st.text_input("Username")
        input_password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login", use_container_width=True)

        if submit_button:
            if not input_username or not input_password:
                st.warning("Please enter both username and password.")
            else:
                user_data = authenticate_user(input_username, input_password)
                
                if user_data:
                    # Save user details to the session memory
                    st.session_state.authenticated = True
                    st.session_state.role = user_data["role"]
                    st.session_state.user_id = user_data["user_id"]
                    st.session_state.username = user_data["username"]
                    
                    st.success("Login Successful! Redirecting...")
                    st.rerun() # Refresh the page to show the "Enter Dashboard" state
                else:
                    st.error("Invalid Username or Password.")
