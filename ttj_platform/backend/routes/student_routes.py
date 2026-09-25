from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
from backend.middleware.auth_deps import get_current_user, require_not_observer
from backend.models.schemas import StudentCreate, StudentUpdate, StudentMove, StudentVacate
from backend.services.student_service import (
    get_students, get_student_detail, create_student,
    update_student, move_student, vacate_student
)
from backend.models.database import get_db, dicts_from_rows

router = APIRouter(prefix="/api/students", tags=["Talabalar"])

@router.get("")
def list_students(search: Optional[str] = None,
                  building_id: Optional[int] = None,
                  block_id: Optional[int] = None,
                  floor_id: Optional[int] = None,
                  room_id: Optional[int] = None,
                  faculty: Optional[str] = None,
                  course: Optional[int] = None,
                  gender: Optional[str] = None,
                  privilege_id: Optional[int] = None,
                  payment_status: Optional[str] = None,
                  sport_id: Optional[int] = None,
                  student_status: Optional[str] = "active",
                  limit: int = 50,
                  offset: int = 0,
                  current_user: dict = Depends(get_current_user)):
    # Manager scope enforcement
    if current_user.get("role_name") == "manager" and current_user.get("assigned_building_id"):
        building_id = current_user.get("assigned_building_id")
        
    return get_students(
        search=search, building_id=building_id, block_id=block_id, floor_id=floor_id,
        room_id=room_id, faculty=faculty, course=course, gender=gender,
        privilege_id=privilege_id, payment_status=payment_status, sport_id=sport_id,
        student_status=student_status, limit=limit, offset=offset, user=current_user
    )

@router.get("/{student_id}")
def student_detail(student_id: int, current_user: dict = Depends(get_current_user)):
    stud = get_student_detail(student_id, current_user)
    if not stud:
        raise HTTPException(status_code=404, detail="Talaba topilmadi")
    return stud

@router.post("")
def add_student(req: StudentCreate, current_user: dict = Depends(require_not_observer)):
    return create_student(req.dict(), current_user)

@router.put("/{student_id}")
def edit_student(student_id: int, req: StudentUpdate, current_user: dict = Depends(require_not_observer)):
    return update_student(student_id, req.dict(exclude_unset=True), current_user)

@router.post("/{student_id}/move")
def transfer_room(student_id: int, req: StudentMove, current_user: dict = Depends(require_not_observer)):
    return move_student(student_id, req.dict(), current_user)

@router.post("/{student_id}/vacate")
def discharge_student(student_id: int, req: StudentVacate, current_user: dict = Depends(require_not_observer)):
    return vacate_student(student_id, req.dict(), current_user)

@router.get("/{student_id}/history")
def student_history(student_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = dicts_from_rows(conn.execute("""
            SELECT * FROM student_history WHERE student_id = ? ORDER BY id DESC
        """, (student_id,)).fetchall())
        return rows
