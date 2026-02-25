from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

router = APIRouter()

# Mocking a global state for now.
# In Phase 6 real integration, this connects to the SQLAlchemy User model.
db_state = {
    "has_users": False
}

@router.get("/setup-status")
def get_setup_status():
    """
    Checks if there are any users in the system.
    If False, the frontend should display the first-time Setup Screen.
    """
    return {"has_users": db_state["has_users"]}

@router.post("/register-admin")
def register_first_admin(data: Dict):
    """
    Registers the first administrator.
    Only allows registration if the database is truly empty.
    """
    if db_state["has_users"]:
        raise HTTPException(status_code=403, detail="System already initialized.")
    
    # Normally we would hash the password and insert to DB here
    db_state["has_users"] = True
    
    return {
        "message": "Admin registered successfully", 
        "token": "mock-jwt-token-admin",
        "user": {
            "name": data.get("name"),
            "email": data.get("email"),
            "role": "admin"
        }
    }

@router.post("/login")
def login(data: Dict):
    """
    Standard Login
    """
    # Mock validation
    if data.get("username") == "admin@empresa.com" and data.get("password") == "1234":
        return {
            "message": "Login successful",
            "token": "mock-jwt-token-admin"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")
