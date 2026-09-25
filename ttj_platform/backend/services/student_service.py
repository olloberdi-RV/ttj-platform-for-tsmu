import datetime
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from backend.models.database import get_db, dicts_from_rows, dict_from_row
from backend.auth.security import mask_jshshir, validate_jshshir, validate_phone
from backend.services.audit_service import log_audit, log_student_history

def get_students(search: Optional[str] = None,
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
                 user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    
    can_view_full = user and user.get("role_name") == "super_admin"
    
    query = """
        SELECT s.*, 
               p.name as privilege_name, p.code as privilege_code,
               sp.name as sport_name,
               r.room_number, r.capacity as room_capacity,
               rb.bed_number,
               b.name as building_name, b.number as building_number,
               blk.name as block_name, blk.block_number,
               f.floor_number
        FROM students s
        LEFT JOIN student_privileges p ON s.privilege_id = p.id
        LEFT JOIN sports sp ON s.sport_id = sp.id
        LEFT JOIN rooms r ON s.current_room_id = r.id
        LEFT JOIN room_beds rb ON s.current_bed_id = rb.id
        LEFT JOIN buildings b ON r.building_id = b.id
        LEFT JOIN blocks blk ON r.block_id = blk.id
        LEFT JOIN floors f ON r.floor_id = f.id
        WHERE s.deleted_at IS NULL
    """
    params = []
    
    if student_status:
        query += " AND s.status = ?"
        params.append(student_status)
    if building_id:
        query += " AND r.building_id = ?"
        params.append(building_id)
    if block_id:
        query += " AND r.block_id = ?"
        params.append(block_id)
    if floor_id:
        query += " AND r.floor_id = ?"
        params.append(floor_id)
    if room_id:
        query += " AND s.current_room_id = ?"
        params.append(room_id)
    if faculty:
        query += " AND s.faculty = ?"
        params.append(faculty)
    if course:
        query += " AND s.course = ?"
        params.append(course)
    if gender:
        query += " AND s.gender = ?"
        params.append(gender)
    if privilege_id:
        query += " AND s.privilege_id = ?"
        params.append(privilege_id)
    if payment_status:
        query += " AND s.payment_status = ?"
        params.append(payment_status)
    if sport_id:
        query += " AND s.sport_id = ?"
        params.append(sport_id)
        
    if search:
        s_clean = search.strip()
        query += """ AND (
            s.full_name LIKE ? OR 
            s.jshshir LIKE ? OR 
            s.phone LIKE ? OR 
            s.faculty LIKE ? OR 
            r.room_number LIKE ? OR 
            b.name LIKE ? OR 
            blk.name LIKE ?
        )"""
        p = f"%{s_clean}%"
        params.extend([p, p, p, p, p, p, p])
        
    # Get total count
    count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
    
    query += " ORDER BY s.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with get_db() as conn:
        total = conn.execute(count_query, params[:-2]).fetchone()["cnt"]
        rows = dicts_from_rows(conn.execute(query, params).fetchall())
        
    for r in rows:
        r["masked_jshshir"] = mask_jshshir(r["jshshir"])
        if not can_view_full:
            r["jshshir"] = r["masked_jshshir"]
            
    return {"total": total, "items": rows}

def get_student_detail(student_id: int, user: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    can_view_full = user and user.get("role_name") == "super_admin"
    with get_db() as conn:
        row = conn.execute("""
            SELECT s.*, 
                   p.name as privilege_name, p.code as privilege_code,
                   sp.name as sport_name,
                   r.room_number, r.capacity as room_capacity,
                   rb.bed_number,
                   b.name as building_name, b.number as building_number, b.id as building_id,
                   blk.name as block_name, blk.block_number, blk.id as block_id,
                   f.floor_number, f.id as floor_id
            FROM students s
            LEFT JOIN student_privileges p ON s.privilege_id = p.id
            LEFT JOIN sports sp ON s.sport_id = sp.id
            LEFT JOIN rooms r ON s.current_room_id = r.id
            LEFT JOIN room_beds rb ON s.current_bed_id = rb.id
            LEFT JOIN buildings b ON r.building_id = b.id
            LEFT JOIN blocks blk ON r.block_id = blk.id
            LEFT JOIN floors f ON r.floor_id = f.id
            WHERE s.id = ? AND s.deleted_at IS NULL
        """, (student_id,)).fetchone()
        
        if not row:
            return None
        student = dict_from_row(row)
        
        # Payments history
        payments = dicts_from_rows(conn.execute("""
            SELECT * FROM payments WHERE student_id = ? ORDER BY payment_date DESC, id DESC
        """, (student_id,)).fetchall())
        student['payments'] = payments
        
        # Accommodation history
        accommodations = dicts_from_rows(conn.execute("""
            SELECT sa.*, r.room_number, rb.bed_number, b.name as building_name, blk.name as block_name, f.floor_number
            FROM student_accommodation sa
            JOIN rooms r ON sa.room_id = r.id
            JOIN room_beds rb ON sa.bed_id = rb.id
            JOIN buildings b ON r.building_id = b.id
            JOIN blocks blk ON r.block_id = blk.id
            JOIN floors f ON r.floor_id = f.id
            WHERE sa.student_id = ?
            ORDER BY sa.id DESC
        """, (student_id,)).fetchall())
        student['accommodation_history'] = accommodations
        
        # Field change history
        history = dicts_from_rows(conn.execute("""
            SELECT * FROM student_history WHERE student_id = ? ORDER BY id DESC
        """, (student_id,)).fetchall())
        student['change_history'] = history
        
        student['masked_jshshir'] = mask_jshshir(student['jshshir'])
        if not can_view_full:
            student['jshshir'] = student['masked_jshshir']
            
        return student

def create_student(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    jshshir = str(data.get("jshshir", "")).strip()
    if not validate_jshshir(jshshir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JShShIR 14 ta raqamdan iborat bo'lishi shart"
        )
    
    room_id = data.get("room_id")
    bed_number = data.get("bed_number")
    
    with get_db() as conn:
        # Check duplicate JShShIR among active students
        existing = conn.execute("""
            SELECT s.id, s.full_name, r.room_number, b.name as building_name
            FROM students s
            LEFT JOIN rooms r ON s.current_room_id = r.id
            LEFT JOIN buildings b ON r.building_id = b.id
            WHERE s.jshshir = ? AND s.status = 'active' AND s.deleted_at IS NULL
        """, (jshshir,)).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ushbu JShShIR bo'yicha faol talaba allaqachon mavjud ({existing['full_name']}, {existing['building_name']} {existing['room_number']}-xona)."
            )
            
        # Check bed existence and availability
        bed = conn.execute("""
            SELECT id, status FROM room_beds WHERE room_id = ? AND bed_number = ?
        """, (room_id, bed_number)).fetchone()
        
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{bed_number}-raqamli o'rin mazkur xonada mavjud emas"
            )
        if bed['status'] != 'vacant':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{bed_number}-o'rin allaqachon band yoki rezerv qilingan"
            )
        bed_id = bed['id']
        
        total_fee = float(data.get("total_fee", 2400000.0))
        paid_fee = float(data.get("paid_fee", 0.0))
        remaining_fee = max(0.0, total_fee - paid_fee)
        payment_status = "paid" if remaining_fee == 0 else ("partial" if paid_fee > 0 else "unpaid")
        check_in_date = data.get("check_in_date") or datetime.date.today().isoformat()
        
        cursor = conn.execute("""
            INSERT INTO students (
                full_name, jshshir, faculty, course, phone, email, gender, birth_date,
                sport_id, other_interests, privilege_id, total_fee, paid_fee, remaining_fee,
                payment_status, status, current_room_id, current_bed_id, check_in_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """, (
            data.get("full_name"),
            jshshir,
            data.get("faculty"),
            int(data.get("course", 1)),
            data.get("phone"),
            data.get("email"),
            data.get("gender", "Erkak"),
            data.get("birth_date"),
            data.get("sport_id"),
            data.get("other_interests"),
            data.get("privilege_id"),
            total_fee,
            paid_fee,
            remaining_fee,
            payment_status,
            room_id,
            bed_id,
            check_in_date
        ))
        student_id = cursor.lastrowid
        
        # Mark bed as occupied
        conn.execute("""
            UPDATE room_beds SET status = 'occupied', current_student_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (student_id, bed_id))
        
        # Accommodation entry
        conn.execute("""
            INSERT INTO student_accommodation (student_id, room_id, bed_id, check_in_date, status, reason, created_by)
            VALUES (?, ?, ?, ?, 'active', 'Dastlabki joylashtirish', ?)
        """, (student_id, room_id, bed_id, check_in_date, current_user.get("full_name")))
        
        # Initial payment record if paid_fee > 0
        if paid_fee > 0:
            conn.execute("""
                INSERT INTO payments (student_id, amount, payment_date, payment_method, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, paid_fee, check_in_date, 'Naqd', "Dastlabki to'lov", current_user.get("full_name")))
            
    log_audit("student_create", "student", student_id, None, {
        "full_name": data.get("full_name"),
        "jshshir": mask_jshshir(jshshir),
        "room_id": room_id,
        "bed_number": bed_number
    }, "Yangi talaba qo'shildi va xonaga joylashtirildi", current_user.get("id"), current_user.get("full_name"))
    
    return {"success": True, "student_id": student_id, "message": "Talaba muvaffaqiyatli ro'yxatga olindi"}

def update_student(student_id: int, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    with get_db() as conn:
        current = conn.execute("SELECT * FROM students WHERE id = ? AND deleted_at IS NULL", (student_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Talaba topilmadi")
            
        old_data = dict_from_row(current)
        updates = []
        params = []
        changes = []
        
        allowed_fields = [
            "full_name", "faculty", "course", "phone", "email", "gender",
            "birth_date", "sport_id", "other_interests", "privilege_id", "total_fee"
        ]
        
        for f in allowed_fields:
            if f in data and data[f] is not None:
                new_val = data[f]
                old_val = old_data.get(f)
                if str(new_val) != str(old_val):
                    updates.append(f"{f} = ?")
                    params.append(new_val)
                    changes.append((f, old_val, new_val))
                    
        if not updates:
            return {"success": True, "message": "O'zgarish kiritilmadi"}
            
        # If total_fee changed, recalculate remaining
        if "total_fee" in data:
            new_total = float(data["total_fee"])
            paid = float(old_data["paid_fee"])
            rem = max(0.0, new_total - paid)
            status_val = "paid" if rem == 0 else ("partial" if paid > 0 else "unpaid")
            updates.extend(["remaining_fee = ?", "payment_status = ?"])
            params.extend([rem, status_val])
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(student_id)
        
        conn.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = ?", params)
        
        reason = data.get("reason", "Talaba ma'lumotlari tahrirlandi")
        for f_name, o_val, n_val in changes:
            log_student_history(student_id, f_name, o_val, n_val, current_user.get("id"), current_user.get("full_name"), "edit", reason, conn=conn)
            
    log_audit("student_update", "student", student_id, old_data, data, reason, current_user.get("id"), current_user.get("full_name"))
    return {"success": True, "message": "Talaba ma'lumotlari yangilandi"}

def move_student(student_id: int, move_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    target_room_id = move_data.get("target_room_id")
    target_bed_number = move_data.get("target_bed_number")
    reason = move_data.get("reason", "Xona almashtirildi")
    
    with get_db() as conn:
        student = conn.execute("""
            SELECT s.*, r.room_number as old_room_number, b.name as old_building_name
            FROM students s
            LEFT JOIN rooms r ON s.current_room_id = r.id
            LEFT JOIN buildings b ON r.building_id = b.id
            WHERE s.id = ? AND s.status = 'active'
        """, (student_id,)).fetchone()
        
        if not student:
            raise HTTPException(status_code=400, detail="Faol talaba topilmadi")
            
        old_room_id = student['current_room_id']
        old_bed_id = student['current_bed_id']
        
        # Check target bed
        target_bed = conn.execute("""
            SELECT rb.id, rb.status, r.room_number, b.name as building_name
            FROM room_beds rb
            JOIN rooms r ON rb.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE rb.room_id = ? AND rb.bed_number = ?
        """, (target_room_id, target_bed_number)).fetchone()
        
        if not target_bed:
            raise HTTPException(status_code=400, detail="Ko'chirilayotgan xona yoki o'rin mavjud emas")
        if target_bed['status'] != 'vacant':
            raise HTTPException(status_code=400, detail="Tanlangan yangi o'rin bo'sh emas")
            
        new_bed_id = target_bed['id']
        now_date = datetime.date.today().isoformat()
        
        # 1. Vacate old bed
        if old_bed_id:
            conn.execute("UPDATE room_beds SET status = 'vacant', current_student_id = NULL WHERE id = ?", (old_bed_id,))
        # 2. Occupy new bed
        conn.execute("UPDATE room_beds SET status = 'occupied', current_student_id = ? WHERE id = ?", (student_id, new_bed_id))
        
        # 3. Update student current room and bed
        conn.execute("""
            UPDATE students 
            SET current_room_id = ?, current_bed_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (target_room_id, new_bed_id, student_id))
        
        # 4. Close previous accommodation record
        conn.execute("""
            UPDATE student_accommodation 
            SET check_out_date = ?, status = 'moved'
            WHERE student_id = ? AND status = 'active'
        """, (now_date, student_id))
        
        # 5. Insert new accommodation record
        conn.execute("""
            INSERT INTO student_accommodation (student_id, room_id, bed_id, check_in_date, status, reason, created_by)
            VALUES (?, ?, ?, ?, 'active', ?, ?)
        """, (student_id, target_room_id, new_bed_id, now_date, reason, current_user.get("full_name")))
        
        desc = f"{student['old_room_number']}-xonadan {target_bed['room_number']}-xonaga ({target_bed_number}-o'rin) ko'chirildi"
        log_student_history(student_id, "room", f"{student['old_room_number']}-xona", f"{target_bed['room_number']}-xona",
                            current_user.get("id"), current_user.get("full_name"), "move", reason, conn=conn)
                            
    log_audit("room_transfer", "student", student_id,
              {"room_id": old_room_id, "bed_id": old_bed_id},
              {"room_id": target_room_id, "bed_id": new_bed_id, "bed_number": target_bed_number},
              desc, current_user.get("id"), current_user.get("full_name"))
              
    return {"success": True, "message": desc}

def vacate_student(student_id: int, vacate_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    new_status = vacate_data.get("status", "vacated")
    reason = vacate_data.get("reason", "TTJdan chiqarildi")
    check_out_date = vacate_data.get("check_out_date") or datetime.date.today().isoformat()
    
    with get_db() as conn:
        student = conn.execute("""
            SELECT s.*, r.room_number FROM students s
            LEFT JOIN rooms r ON s.current_room_id = r.id
            WHERE s.id = ? AND s.deleted_at IS NULL
        """, (student_id,)).fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Talaba topilmadi")
            
        old_bed_id = student['current_bed_id']
        old_room_number = student['room_number']
        
        # Free bed
        if old_bed_id:
            conn.execute("UPDATE room_beds SET status = 'vacant', current_student_id = NULL WHERE id = ?", (old_bed_id,))
            
        # Update student record
        conn.execute("""
            UPDATE students 
            SET status = ?, current_room_id = NULL, current_bed_id = NULL,
                check_out_date = ?, vacate_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, check_out_date, reason, student_id))
        
        # Close accommodation record
        conn.execute("""
            UPDATE student_accommodation 
            SET check_out_date = ?, status = 'vacated', reason = ?
            WHERE student_id = ? AND status = 'active'
        """, (check_out_date, reason, student_id))
        
        log_student_history(student_id, "status", student['status'], new_status,
                            current_user.get("id"), current_user.get("full_name"), "vacate", reason, conn=conn)
                            
    log_audit("student_vacate", "student", student_id,
              {"status": student['status'], "room_id": student['current_room_id']},
              {"status": new_status, "vacate_reason": reason},
              f"Talaba {old_room_number}-xonadan chiqarildi (Sabab: {reason})",
              current_user.get("id"), current_user.get("full_name"))
              
    return {"success": True, "message": "Talaba TTJdan muvaffaqiyatli chiqarildi, o'rin bo'shatildi"}
