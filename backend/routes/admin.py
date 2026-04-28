from fastapi import APIRouter
from db import execute_query
from schemas.farmer_schema import AddParcelRequest
import json

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/addfarmer")
def create_farmer(username: str, email: str, passwordHash: str):

    # -------------------------
    # 1. Check if user exists
    # -------------------------
    existing_user = execute_query(
        "SELECT * FROM user_accounts WHERE email = %s",
        (email,),
        fetch=True
    )

    if existing_user:
        return {"error": "User with this email already exists"}

    # -------------------------
    # 2. Insert into user_accounts
    # -------------------------
    user_query = """
        INSERT INTO user_accounts (username, passwordhash, email, roletype, accountstatus)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING userid;
    """

    user_result = execute_query(
        user_query,
        (username, passwordHash, email, "Farmer", "Active"),
        fetch=True
    )

    user_id = user_result[0]["userid"] # type: ignore

    # -------------------------
    # 3. Insert into Farmers table
    # -------------------------
    farmer_query = """
        INSERT INTO Farmers (userid, registrationdate)
        VALUES (%s, CURRENT_DATE)
        RETURNING userid;
    """

    farmer_result = execute_query(
        farmer_query,
        (user_id,),
        fetch=True
    )

    return {
        "message": "Farmer created successfully",
        "user_id": user_id,
        "farmer_id": farmer_result[0]["userid"] # type: ignore
    }