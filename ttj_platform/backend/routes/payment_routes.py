from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from backend.middleware.auth_deps import get_current_user, require_not_observer
from backend.models.schemas import PaymentCreate
from backend.services.payment_service import record_payment, get_payments_list

router = APIRouter(prefix="/api/payments", tags=["To'lovlar"])

@router.get("")
def list_payments(student_id: Optional[int] = None,
                  search: Optional[str] = None,
                  limit: int = 50,
                  offset: int = 0,
                  current_user: dict = Depends(get_current_user)):
    return get_payments_list(student_id, search, limit, offset)

@router.post("")
def add_payment(req: PaymentCreate, current_user: dict = Depends(require_not_observer)):
    return record_payment(req.dict(), current_user)

@router.get("/student/{student_id}")
def student_payments(student_id: int, current_user: dict = Depends(get_current_user)):
    return get_payments_list(student_id=student_id)
