from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {
        "widget": "demo",
        "status": "active",
        "message": "Demo widget is running correctly via autodiscovery!"
    }
