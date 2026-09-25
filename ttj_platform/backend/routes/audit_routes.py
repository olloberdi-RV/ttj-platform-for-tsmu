from fastapi import APIRouter, Depends, Query
from typing import Optional
from backend.middleware.auth_deps import get_current_user, require_role
from backend.services.audit_service import get_audit_logs

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Log"])

@router.get("")
def list_audit_logs(limit: int = 50, offset: int = 0,
                    entity_type: Optional[str] = None,
                    action: Optional[str] = None,
                    current_user: dict = Depends(get_current_user)):
    return get_audit_logs(limit, offset, entity_type, action)
