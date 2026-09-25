import json
import datetime
from backend.models.database import get_db, dicts_from_rows
from backend.services.audit_service import log_audit

TABLES = [
    "roles", "users", "buildings", "blocks", "floors", "rooms",
    "room_beds", "sports", "student_privileges", "students",
    "student_accommodation", "payments", "audit_logs", "imports",
    "import_errors", "student_history"
]

def create_backup_json() -> str:
    backup_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0",
        "system": "TTJ Boshqaruv Tizimi",
        "tables": {}
    }
    with get_db() as conn:
        for t in TABLES:
            cursor = conn.execute(f"SELECT * FROM {t}")
            backup_data["tables"][t] = dicts_from_rows(cursor.fetchall())
            
    return json.dumps(backup_data, ensure_ascii=False, indent=2)

def restore_backup_json(json_str: str, current_user: dict) -> dict:
    data = json.loads(json_str)
    tables_data = data.get("tables", {})
    if not tables_data:
        raise ValueError("Zaxira nusxasida jadvallar ma'lumoti topilmadi")
        
    with get_db() as conn:
        # Disable foreign keys during restore
        conn.execute("PRAGMA foreign_keys = OFF;")
        
        for t in reversed(TABLES):
            conn.execute(f"DELETE FROM {t}")
            
        for t in TABLES:
            rows = tables_data.get(t, [])
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            insert_sql = f"INSERT INTO {t} ({col_names}) VALUES ({placeholders})"
            
            for r in rows:
                conn.execute(insert_sql, [r[c] for c in cols])
                
        conn.execute("PRAGMA foreign_keys = ON;")
        
    log_audit("backup_restore", "system", None, None, {"timestamp": data.get("timestamp")},
              "Ma'lumotlar bazasi zaxira nusxadan tiklandi", current_user.get("id"), current_user.get("full_name"))
              
    return {"success": True, "message": "Ma'lumotlar bazasi muvaffaqiyatli tiklandi"}
