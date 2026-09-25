from backend.models.database import get_db, dicts_from_rows, dict_from_row
from backend.auth.security import mask_jshshir
from typing import Dict, Any, List

def get_dashboard_stats() -> Dict[str, Any]:
    with get_db() as conn:
        # Building, Block, Floor, Room counts
        b_count = conn.execute("SELECT COUNT(*) as c FROM buildings WHERE deleted_at IS NULL").fetchone()['c']
        blk_count = conn.execute("SELECT COUNT(*) as c FROM blocks WHERE deleted_at IS NULL").fetchone()['c']
        flr_count = conn.execute("SELECT COUNT(*) as c FROM floors WHERE deleted_at IS NULL").fetchone()['c']
        room_count = conn.execute("SELECT COUNT(*) as c FROM rooms WHERE deleted_at IS NULL").fetchone()['c']
        
        # Bed stats
        bed_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_beds,
                SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied_beds,
                SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) as vacant_beds,
                SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved_beds
            FROM room_beds
        """).fetchone()
        
        total_beds = bed_stats['total_beds'] or 0
        occupied_beds = bed_stats['occupied_beds'] or 0
        vacant_beds = bed_stats['vacant_beds'] or 0
        reserved_beds = bed_stats['reserved_beds'] or 0
        occupancy_rate = round((occupied_beds / total_beds) * 100, 1) if total_beds > 0 else 0
        
        # Student count & Financial stats
        fin_stats = conn.execute("""
            SELECT 
                COUNT(*) as active_students,
                SUM(total_fee) as total_fee,
                SUM(paid_fee) as paid_fee,
                SUM(remaining_fee) as debt_fee,
                SUM(CASE WHEN remaining_fee > 0 THEN 1 ELSE 0 END) as debtor_count
            FROM students
            WHERE status = 'active' AND deleted_at IS NULL
        """).fetchone()
        
        active_students = fin_stats['active_students'] or 0
        total_fee = fin_stats['total_fee'] or 0.0
        paid_fee = fin_stats['paid_fee'] or 0.0
        debt_fee = fin_stats['debt_fee'] or 0.0
        debtor_count = fin_stats['debtor_count'] or 0
        
        # Faculty distribution
        faculties = dicts_from_rows(conn.execute("""
            SELECT faculty as name, COUNT(*) as count, SUM(paid_fee) as paid, SUM(remaining_fee) as debt
            FROM students WHERE status = 'active' AND deleted_at IS NULL
            GROUP BY faculty ORDER BY count DESC
        """).fetchall())
        
        # Course distribution
        courses = dicts_from_rows(conn.execute("""
            SELECT course as name, COUNT(*) as count
            FROM students WHERE status = 'active' AND deleted_at IS NULL
            GROUP BY course ORDER BY course ASC
        """).fetchall())
        
        # Privilege distribution
        privileges = dicts_from_rows(conn.execute("""
            SELECT p.name, COUNT(s.id) as count
            FROM student_privileges p
            LEFT JOIN students s ON s.privilege_id = p.id AND s.status = 'active' AND s.deleted_at IS NULL
            GROUP BY p.id ORDER BY count DESC
        """).fetchall())
        
        # Building occupancy breakdown
        building_occupancy = dicts_from_rows(conn.execute("""
            SELECT b.name as building_name, b.number,
                   COUNT(rb.id) as total_beds,
                   SUM(CASE WHEN rb.status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                   SUM(CASE WHEN rb.status = 'vacant' THEN 1 ELSE 0 END) as vacant
            FROM buildings b
            JOIN rooms r ON r.building_id = b.id
            JOIN room_beds rb ON rb.room_id = r.id
            WHERE b.deleted_at IS NULL AND r.deleted_at IS NULL
            GROUP BY b.id
            ORDER BY b.number ASC
        """).fetchall())
        
        for bo in building_occupancy:
            bo['rate'] = round((bo['occupied'] / bo['total_beds']) * 100, 1) if bo['total_beds'] > 0 else 0
            
        # Top Debtors
        debtors = dicts_from_rows(conn.execute("""
            SELECT s.id, s.full_name, s.jshshir, s.phone, s.faculty, s.course,
                   s.total_fee, s.paid_fee, s.remaining_fee,
                   r.room_number, b.name as building_name
            FROM students s
            LEFT JOIN rooms r ON s.current_room_id = r.id
            LEFT JOIN buildings b ON r.building_id = b.id
            WHERE s.status = 'active' AND s.remaining_fee > 0 AND s.deleted_at IS NULL
            ORDER BY s.remaining_fee DESC LIMIT 6
        """).fetchall())
        
        for d in debtors:
            d['masked_jshshir'] = mask_jshshir(d['jshshir'])
            
        # Recent audit logs
        recent_logs = dicts_from_rows(conn.execute("""
            SELECT * FROM audit_logs ORDER BY id DESC LIMIT 6
        """).fetchall())
        
        # Notifications / Alerts
        alerts = []
        if occupancy_rate >= 80:
            alerts.append({
                "type": "warning",
                "title": "Xonalar to'lib bormoqda",
                "message": f"TTJ umumiy bandlik ko'rsatkichi {occupancy_rate}% ga yetdi. Bo'sh o'rinlar soni: {vacant_beds} ta."
            })
        if debt_fee > 0:
            alerts.append({
                "type": "danger",
                "title": "To'lov qarzdorligi mavjud",
                "message": f"{debtor_count} nafar talabada jami {debt_fee:,.0f} so'm to'lov qarzdorligi aniqlandi."
            })
            
        # Check recent import errors
        recent_imp = conn.execute("SELECT * FROM imports WHERE error_count > 0 ORDER BY id DESC LIMIT 1").fetchone()
        if recent_imp:
            alerts.append({
                "type": "info",
                "title": "So'nggi importda xatoliklar qayd etilgan",
                "message": f"'{recent_imp['file_name']}' faylidan {recent_imp['error_count']} ta qatorda xatolik aniqlangan."
            })
            
        return {
            "counts": {
                "buildings": b_count,
                "blocks": blk_count,
                "floors": flr_count,
                "rooms": room_count,
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "reserved_beds": reserved_beds,
                "occupancy_rate": occupancy_rate,
                "active_students": active_students,
                "total_fee": total_fee,
                "paid_fee": paid_fee,
                "debt_fee": debt_fee,
                "debtor_count": debtor_count
            },
            "charts": {
                "faculties": faculties,
                "courses": courses,
                "privileges": privileges,
                "building_occupancy": building_occupancy
            },
            "debtors": debtors,
            "recent_logs": recent_logs,
            "alerts": alerts
        }
