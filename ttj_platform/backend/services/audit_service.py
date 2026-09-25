import json
from typing import Optional, Dict, Any
from backend.models.database import get_db, dicts_from_rows

def log_audit(action: str, entity_type: str, entity_id: Optional[int] = None,
              old_values: Optional[Dict[str, Any]] = None,
              new_values: Optional[Dict[str, Any]] = None,
              reason: Optional[str] = None,
              user_id: Optional[int] = None,
              user_name: Optional[str] = None,
              ip_address: Optional[str] = None,
              conn: Optional[Any] = None):
    if conn is None:
        with get_db() as c:
            log_audit(action, entity_type, entity_id, old_values, new_values, reason, user_id, user_name, ip_address, conn=c)
        return
        
    conn.execute("""
        INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, old_values, new_values, reason, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        user_name or "Tizim",
        action,
        entity_type,
        entity_id,
        json.dumps(old_values, ensure_ascii=False) if old_values else None,
        json.dumps(new_values, ensure_ascii=False) if new_values else None,
        reason,
        ip_address
    ))

def log_student_history(student_id: int, field_name: str, old_value: Any, new_value: Any,
                        user_id: Optional[int] = None, user_name: Optional[str] = None,
                        action_type: str = "edit", reason: Optional[str] = None,
                        conn: Optional[Any] = None):
    if conn is None:
        with get_db() as c:
            log_student_history(student_id, field_name, old_value, new_value, user_id, user_name, action_type, reason, conn=c)
        return
        
    conn.execute("""
        INSERT INTO student_history (student_id, field_name, old_value, new_value, user_id, user_name, action_type, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        field_name,
        str(old_value) if old_value is not None else "",
        str(new_value) if new_value is not None else "",
        user_id,
        user_name or "Administrator",
        action_type,
        reason
    ))

def get_audit_logs(limit: int = 50, offset: int = 0, entity_type: Optional[str] = None, action: Optional[str] = None):
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    if action:
        query += " AND action = ?"
        params.append(action)
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with get_db() as conn:
        cursor = conn.execute(query, params)
        rows = dicts_from_rows(cursor.fetchall())
        count_cursor = conn.execute("SELECT COUNT(*) as count FROM audit_logs")
        total = count_cursor.fetchone()["count"]
        
    for r in rows:
        if r.get("old_values"):
            try:
                r["old_values"] = json.loads(r["old_values"])
            except Exception:
                pass
        if r.get("new_values"):
            try:
                r["new_values"] = json.loads(r["new_values"])
            except Exception:
                pass
    return {"total": total, "items": rows}
