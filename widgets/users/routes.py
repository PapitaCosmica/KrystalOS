from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()
WIDGET_DIR = os.path.dirname(os.path.abspath(__file__))

@router.get("/ui")
def get_user_ui():
    """Returns the main UI HTML for the Users widget"""
    return FileResponse(os.path.join(WIDGET_DIR, "ui.html"))

@router.get("/list")
def list_users():
    """Mock API for listing users"""
    return [
        {"id": 1, "name": "Admin Principal", "email": "admin@empresa.com", "role": "admin"},
        {"id": 2, "name": "Juan Perez", "email": "jperez@empresa.com", "role": "user"}
    ]
