from fastapi import APIRouter, Depends
from backend.middleware.auth_deps import get_current_user
from backend.services.reference_service import get_reference_data

router = APIRouter(prefix="/api/reference-data", tags=["Ma'lumotnomalar"])

@router.get("")
def reference_data(current_user: dict = Depends(get_current_user)):
    return get_reference_data()
