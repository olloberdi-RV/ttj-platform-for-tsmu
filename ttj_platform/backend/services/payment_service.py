from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from backend.models.database import get_db, dicts_from_rows, dict_from_row
from backend.services.audit_service import log_audit, log_student_history

def record_payment(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    student_id = data.get("student_id")
    amount = float(data.get("amount", 0.0))
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To'lov summasi musbat son bo'lishi kerak"
        )
    payment_date = data.get("payment_date")
    payment_method = data.get("payment_method", "Naqd")
    receipt_number = data.get("receipt_number")
    notes = data.get("notes")
    
    with get_db() as conn:
        student = conn.execute("SELECT * FROM students WHERE id = ? AND deleted_at IS NULL", (student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Talaba topilmadi")
            
        old_paid = float(student["paid_fee"])
        total_fee = float(student["total_fee"])
        
        cursor = conn.execute("""
            INSERT INTO payments (student_id, amount, payment_date, payment_method, receipt_number, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, amount, payment_date, payment_method, receipt_number, notes, current_user.get("full_name")))
        payment_id = cursor.lastrowid
        
        new_paid = old_paid + amount
        new_remaining = max(0.0, total_fee - new_paid)
        new_status = "paid" if new_remaining == 0 else ("partial" if new_paid > 0 else "unpaid")
        
        conn.execute("""
            UPDATE students 
            SET paid_fee = ?, remaining_fee = ?, payment_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_paid, new_remaining, new_status, student_id))
        
        desc = f"To'lov kiritildi: {amount:,.0f} so'm ({payment_method})"
        
    log_student_history(student_id, "paid_fee", f"{old_paid:,.0f} so'm", f"{new_paid:,.0f} so'm",
                        current_user.get("id"), current_user.get("full_name"), "payment", desc)
                        
    log_audit("payment_create", "payment", payment_id,
              {"old_paid": old_paid},
              {"amount": amount, "new_paid": new_paid, "new_remaining": new_remaining},
              desc, current_user.get("id"), current_user.get("full_name"))
              
    return {
        "success": True,
        "payment_id": payment_id,
        "new_paid": new_paid,
        "new_remaining": new_remaining,
        "payment_status": new_status,
        "message": "To'lov muvaffaqiyatli saqlandi"
    }

def get_payments_list(student_id: Optional[int] = None, search: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    with get_db() as conn:
        query = """
            SELECT p.*, s.full_name as student_name, s.jshshir as student_jshshir,
                   s.faculty, s.course, r.room_number, b.name as building_name
            FROM payments p
            JOIN students s ON p.student_id = s.id
            LEFT JOIN rooms r ON s.current_room_id = r.id
            LEFT JOIN buildings b ON r.building_id = b.id
            WHERE 1=1
        """
        params = []
        if student_id:
            query += " AND p.student_id = ?"
            params.append(student_id)
        if search:
            query += " AND (s.full_name LIKE ? OR s.jshshir LIKE ? OR p.receipt_number LIKE ?)"
            s_param = f"%{search.strip()}%"
            params.extend([s_param, s_param, s_param])
            
        count_q = f"SELECT COUNT(*) as cnt FROM ({query})"
        total = conn.execute(count_q, params).fetchone()["cnt"]
        
        query += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = dicts_from_rows(conn.execute(query, params).fetchall())
        
        return {"total": total, "items": rows}
