from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]

class ResetPasswordRequest(BaseModel):
    username: str
    email: Optional[str] = None
    new_password: str

class StudentCreate(BaseModel):
    full_name: str
    jshshir: str
    faculty: str
    course: int
    phone: str
    email: Optional[str] = None
    gender: str # 'Erkak' or 'Ayol'
    birth_date: Optional[str] = None
    sport_id: Optional[int] = None
    other_interests: Optional[str] = None
    privilege_id: Optional[int] = None
    total_fee: Optional[float] = 2400000.0
    paid_fee: Optional[float] = 0.0
    building_id: int
    block_id: int
    floor_id: int
    room_id: int
    bed_number: int
    check_in_date: Optional[str] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    sport_id: Optional[int] = None
    other_interests: Optional[str] = None
    privilege_id: Optional[int] = None
    total_fee: Optional[float] = None
    notes: Optional[str] = None
    reason: Optional[str] = "Ma'lumotlar tahrirlandi"

class StudentMove(BaseModel):
    target_building_id: int
    target_block_id: int
    target_floor_id: int
    target_room_id: int
    target_bed_number: int
    reason: Optional[str] = "Xona almashtirildi"

class StudentVacate(BaseModel):
    status: str = "vacated" # 'vacated', 'graduated', 'academic_leave', 'other'
    reason: str
    check_out_date: Optional[str] = None

class PaymentCreate(BaseModel):
    student_id: int
    amount: float
    payment_date: str
    payment_method: str = "Naqd" # 'Naqd', 'Plastik karta', 'Payme/Click', 'Bank o\'tkazmasi'
    receipt_number: Optional[str] = None
    notes: Optional[str] = None

class BuildingCreate(BaseModel):
    name: str
    number: str
    address: Optional[str] = None
    total_floors: Optional[int] = 1
    notes: Optional[str] = None

class BlockCreate(BaseModel):
    building_id: int
    name: str
    block_number: str
    notes: Optional[str] = None

class FloorCreate(BaseModel):
    block_id: int
    floor_number: int
    total_rooms: Optional[int] = 0

class RoomCreate(BaseModel):
    building_id: int
    block_id: int
    floor_id: int
    room_number: str
    room_type: Optional[str] = "oddiy"
    capacity: int = 4
    notes: Optional[str] = None
