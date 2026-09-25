from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from backend.auth.security import security_bearer, decode_access_token
from backend.models.database import get_db, dict_from_row

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tizimga kirish talab etiladi (Token topilmadi)"
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessiya eskirgan yoki yaroqsiz token"
        )
    user_id = payload.get("sub")
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT u.*, r.name as role_name, r.display_name as role_display
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = ? AND u.is_active = 1
        """, (user_id,))
        user = dict_from_row(cursor.fetchone())
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi yoki hisob bloklangan"
        )
    return user

def require_role(allowed_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        role_name = current_user.get("role_name")
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu amalni bajarish uchun sizda yetarli ruxsat yo'q"
            )
        return current_user
    return role_checker

def require_not_observer(current_user: dict = Depends(get_current_user)):
    if current_user.get("role_name") == "observer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kuzatuvchi roliga ma'lumotlarni o'zgartirish yoki o'chirish taqiqlangan"
        )
    return current_user
