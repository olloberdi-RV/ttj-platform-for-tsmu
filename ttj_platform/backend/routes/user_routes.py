from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from backend.middleware.auth_deps import require_role, get_current_user
from backend.models.database import get_db, dicts_from_rows
from backend.auth.security import hash_password, generate_salt
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/api/users", tags=["Foydalanuvchilar"])

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: int
    assigned_building_id: Optional[int] = None
    assigned_block_id: Optional[int] = None
    assigned_floor_id: Optional[int] = None

@router.get("")
def list_users(current_user: dict = Depends(require_role(["super_admin"]))):
    with get_db() as conn:
        users = dicts_from_rows(conn.execute("""
            SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role_id,
                   u.assigned_building_id, u.assigned_block_id, u.assigned_floor_id,
                   u.is_active, u.last_login, u.created_at,
                   r.name as role_name, r.display_name as role_display,
                   b.name as assigned_building_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN buildings b ON u.assigned_building_id = b.id
            ORDER BY u.id ASC
        """).fetchall())
        return users

@router.post("")
def create_user(req: UserCreate, current_user: dict = Depends(require_role(["super_admin"]))):
    username = req.username.strip().lower()
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Bunday foydalanuvchi nomi (username) allaqachon mavjud")
            
        salt = generate_salt()
        pwd_hash = hash_password(req.password, salt)
        
        cursor = conn.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, email, phone, role_id,
                               assigned_building_id, assigned_block_id, assigned_floor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, pwd_hash, salt, req.full_name, req.email, req.phone, req.role_id,
            req.assigned_building_id, req.assigned_block_id, req.assigned_floor_id
        ))
        user_id = cursor.lastrowid
        
    log_audit("user_create", "user", user_id, None, {"username": username, "role_id": req.role_id},
              f"Yangi foydalanuvchi yaratildi: {req.full_name}", current_user['id'], current_user['full_name'])
              
    return {"id": user_id, "message": "Foydalanuvchi muvaffaqiyatli yaratildi"}
