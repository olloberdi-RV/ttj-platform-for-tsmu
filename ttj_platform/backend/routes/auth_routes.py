from fastapi import APIRouter, HTTPException, Depends, status, Request
from backend.models.schemas import LoginRequest, ResetPasswordRequest
from backend.models.database import get_db, dict_from_row
from backend.auth.security import verify_password, hash_password, generate_salt, create_access_token
from backend.middleware.auth_deps import get_current_user
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/api/auth", tags=["Autentifikatsiya"])

@router.post("/login")
def login(req: LoginRequest, request: Request):
    username = req.username.strip()
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT u.*, r.name as role_name, r.display_name as role_display
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = ? AND u.is_active = 1
        """, (username,))
        user = dict_from_row(cursor.fetchone())
        
    if not user:
        raise HTTPException(status_code=400, detail="Login yoki parol noto'g'ri")
        
    if not verify_password(req.password, user['salt'], user['password_hash']):
        raise HTTPException(status_code=400, detail="Login yoki parol noto'g'ri")
        
    # Update last login
    with get_db() as conn:
        conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
        
    token = create_access_token({
        "sub": user['id'],
        "username": user['username'],
        "role": user['role_name'],
        "full_name": user['full_name']
    }, expires_in=86400 * 30 if req.remember_me else 86400 * 7)
    
    log_audit("user_login", "user", user['id'], None, None, "Tizimga muvaffaqiyatli kirdi",
              user['id'], user['full_name'], request.client.host if request.client else None)
              
    safe_user = {
        "id": user['id'],
        "username": user['username'],
        "full_name": user['full_name'],
        "email": user['email'],
        "phone": user['phone'],
        "role": user['role_name'],
        "role_display": user['role_display'],
        "assigned_building_id": user['assigned_building_id'],
        "assigned_block_id": user['assigned_block_id'],
        "assigned_floor_id": user['assigned_floor_id']
    }
    return {"token": token, "user": safe_user}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "username": current_user['username'],
        "full_name": current_user['full_name'],
        "email": current_user['email'],
        "phone": current_user['phone'],
        "role": current_user['role_name'],
        "role_display": current_user['role_display'],
        "assigned_building_id": current_user['assigned_building_id'],
        "assigned_block_id": current_user['assigned_block_id'],
        "assigned_floor_id": current_user['assigned_floor_id']
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (req.username.strip(),)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Bunday foydalanuvchi topilmadi")
            
        salt = generate_salt()
        pwd_hash = hash_password(req.new_password, salt)
        
        conn.execute("UPDATE users SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (pwd_hash, salt, user['id']))
                     
    log_audit("password_reset", "user", user['id'], None, None, "Parol qayta tiklandi",
              user['id'], user['full_name'], request.client.host if request.client else None)
              
    return {"success": True, "message": "Parol muvaffaqiyatli yangilandi"}
