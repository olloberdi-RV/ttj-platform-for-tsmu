from fastapi import APIRouter, Depends
from backend.middleware.auth_deps import get_current_user
from backend.services.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def dashboard_stats(current_user: dict = Depends(get_current_user)):
    return get_dashboard_stats()
