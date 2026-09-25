import hashlib
import hmac
import base64
import json
import time
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os_secret = "ttj_ultra_secure_secret_key_2026_tashkent_med"
TOKEN_EXPIRY_SECONDS = 86400 * 7 # 7 days

security_bearer = HTTPBearer(auto_error=False)

def generate_salt() -> str:
    return secrets.token_hex(16)

def hash_password(password: str, salt: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return key.hex()

def verify_password(password: str, salt: str, password_hash: str) -> bool:
    expected_hash = hash_password(password, salt)
    return hmac.compare_digest(expected_hash, password_hash)

def create_access_token(data: Dict[str, Any], expires_in: int = TOKEN_EXPIRY_SECONDS) -> str:
    payload = data.copy()
    payload['exp'] = int(time.time()) + expires_in
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + '=' * (-len(sig_b64) % 4))
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload_json = base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4)).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get('exp', 0) < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None

def mask_jshshir(jshshir: str) -> str:
    if not jshshir:
        return ""
    clean = str(jshshir).strip()
    if len(clean) >= 4:
        return "********" + clean[-4:]
    return "********"

def validate_jshshir(jshshir: str) -> bool:
    if not jshshir:
        return False
    clean = str(jshshir).strip()
    return len(clean) == 14 and clean.isdigit()

def validate_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = "".join(filter(str.isdigit, str(phone)))
    # Uzbekistan phones: 998XXXXXXXXX (12 digits) or 9 digits local
    return len(digits) in (9, 12)
