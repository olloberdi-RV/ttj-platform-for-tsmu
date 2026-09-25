from backend.models.database import get_db, dicts_from_rows, dict_from_row
from typing import List, Dict, Any, Optional

def get_buildings_hierarchy(user_building_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        b_query = "SELECT * FROM buildings WHERE deleted_at IS NULL"
        params = []
        if user_building_id:
            b_query += " AND id = ?"
            params.append(user_building_id)
        b_query += " ORDER BY number ASC, name ASC"
        
        buildings = dicts_from_rows(conn.execute(b_query, params).fetchall())
        for b in buildings:
            blocks = dicts_from_rows(conn.execute("""
                SELECT * FROM blocks WHERE building_id = ? AND deleted_at IS NULL ORDER BY block_number ASC
            """, (b['id'],)).fetchall())
            
            for blk in blocks:
                floors = dicts_from_rows(conn.execute("""
                    SELECT * FROM floors WHERE block_id = ? AND deleted_at IS NULL ORDER BY floor_number ASC
                """, (blk['id'],)).fetchall())
                blk['floors'] = floors
            b['blocks'] = blocks
    return buildings

def get_rooms(building_id: Optional[int] = None, block_id: Optional[int] = None,
              floor_id: Optional[int] = None, search: Optional[str] = None,
              status_filter: Optional[str] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    with get_db() as conn:
        query = """
            SELECT r.*, 
                   b.name as building_name, b.number as building_number,
                   blk.name as block_name, blk.block_number,
                   f.floor_number,
                   (SELECT COUNT(*) FROM room_beds rb WHERE rb.room_id = r.id AND rb.status = 'occupied') as occupied_count,
                   (SELECT COUNT(*) FROM room_beds rb WHERE rb.room_id = r.id AND rb.status = 'vacant') as vacant_count,
                   (SELECT COUNT(*) FROM room_beds rb WHERE rb.room_id = r.id AND rb.status = 'reserved') as reserved_count
            FROM rooms r
            JOIN buildings b ON r.building_id = b.id
            JOIN blocks blk ON r.block_id = blk.id
            JOIN floors f ON r.floor_id = f.id
            WHERE r.deleted_at IS NULL
        """
        params = []
        if building_id:
            query += " AND r.building_id = ?"
            params.append(building_id)
        if block_id:
            query += " AND r.block_id = ?"
            params.append(block_id)
        if floor_id:
            query += " AND r.floor_id = ?"
            params.append(floor_id)
        if search:
            query += " AND (r.room_number LIKE ? OR b.name LIKE ? OR blk.name LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param])
            
        query += " ORDER BY b.number, blk.block_number, f.floor_number, r.room_number ASC"
        
        all_rooms = dicts_from_rows(conn.execute(query, params).fetchall())
        
        # Apply bed status filter if requested
        filtered = []
        for r in all_rooms:
            r['occupancy_rate'] = round((r['occupied_count'] / r['capacity']) * 100, 1) if r['capacity'] > 0 else 0
            
            # Fetch bed dots
            beds = dicts_from_rows(conn.execute("""
                SELECT bed_number, status FROM room_beds WHERE room_id = ? ORDER BY bed_number ASC
            """, (r['id'],)).fetchall())
            r['beds'] = beds
            
            if status_filter == 'vacant' and r['vacant_count'] == 0:
                continue
            if status_filter == 'occupied' and r['vacant_count'] > 0:
                continue
            filtered.append(r)
            
        total = len(filtered)
        paginated = filtered[offset:offset+limit]
        return {"total": total, "items": paginated}

def get_room_details(room_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        room_row = conn.execute("""
            SELECT r.*, 
                   b.name as building_name, b.number as building_number,
                   blk.name as block_name, blk.block_number,
                   f.floor_number
            FROM rooms r
            JOIN buildings b ON r.building_id = b.id
            JOIN blocks blk ON r.block_id = blk.id
            JOIN floors f ON r.floor_id = f.id
            WHERE r.id = ? AND r.deleted_at IS NULL
        """, (room_id,)).fetchone()
        
        if not room_row:
            return None
            
        room = dict_from_row(room_row)
        
        beds = dicts_from_rows(conn.execute("""
            SELECT rb.*,
                   s.full_name as student_name, s.jshshir as student_jshshir,
                   s.faculty as student_faculty, s.course as student_course,
                   s.phone as student_phone, s.payment_status as student_payment_status,
                   s.paid_fee, s.remaining_fee, s.total_fee
            FROM room_beds rb
            LEFT JOIN students s ON rb.current_student_id = s.id
            WHERE rb.room_id = ?
            ORDER BY rb.bed_number ASC
        """, (room_id,)).fetchall())
        
        occupied = sum(1 for b in beds if b['status'] == 'occupied')
        vacant = sum(1 for b in beds if b['status'] == 'vacant')
        reserved = sum(1 for b in beds if b['status'] == 'reserved')
        
        room['beds'] = beds
        room['occupied_count'] = occupied
        room['vacant_count'] = vacant
        room['reserved_count'] = reserved
        room['occupancy_percentage'] = round((occupied / room['capacity']) * 100, 1) if room['capacity'] > 0 else 0
        return room

def get_floor_grid(floor_id: int) -> Dict[str, Any]:
    with get_db() as conn:
        floor_info = dict_from_row(conn.execute("""
            SELECT f.*, blk.name as block_name, b.name as building_name, b.number as building_number
            FROM floors f
            JOIN blocks blk ON f.block_id = blk.id
            JOIN buildings b ON blk.building_id = b.id
            WHERE f.id = ?
        """, (floor_id,)).fetchone())
        
        if not floor_info:
            return {}
            
        rooms = dicts_from_rows(conn.execute("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM room_beds rb WHERE rb.room_id = r.id AND rb.status = 'occupied') as occupied_count,
                   (SELECT COUNT(*) FROM room_beds rb WHERE rb.room_id = r.id AND rb.status = 'vacant') as vacant_count
            FROM rooms r
            WHERE r.floor_id = ? AND r.deleted_at IS NULL
            ORDER BY r.room_number ASC
        """, (floor_id,)).fetchall())
        
        for r in rooms:
            beds = dicts_from_rows(conn.execute("""
                SELECT bed_number, status, current_student_id FROM room_beds WHERE room_id = ? ORDER BY bed_number ASC
            """, (r['id'],)).fetchall())
            r['beds'] = beds
            
        floor_info['rooms'] = rooms
        return floor_info
