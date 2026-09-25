from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from backend.middleware.auth_deps import get_current_user, require_not_observer
from backend.services.building_service import get_buildings_hierarchy, get_rooms, get_room_details, get_floor_grid
from backend.models.schemas import BuildingCreate, BlockCreate, FloorCreate, RoomCreate
from backend.models.database import get_db, dicts_from_rows, dict_from_row
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/api", tags=["Bino va Xonalar"])

@router.get("/buildings/hierarchy")
def list_hierarchy(current_user: dict = Depends(get_current_user)):
    user_b_id = current_user.get("assigned_building_id") if current_user.get("role_name") == "manager" else None
    return get_buildings_hierarchy(user_b_id)

@router.get("/buildings")
def list_buildings(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        q = "SELECT * FROM buildings WHERE deleted_at IS NULL ORDER BY number ASC, name ASC"
        return dicts_from_rows(conn.execute(q).fetchall())

@router.post("/buildings")
def create_building(req: BuildingCreate, current_user: dict = Depends(require_not_observer)):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO buildings (name, number, address, total_floors, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (req.name, req.number, req.address, req.total_floors, req.notes))
        b_id = cursor.lastrowid
    log_audit("building_create", "building", b_id, None, req.dict(), "Yangi bino qo'shildi",
              current_user['id'], current_user['full_name'])
    return {"id": b_id, "message": "Bino yaratildi"}

@router.get("/blocks")
def list_blocks(building_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        q = "SELECT * FROM blocks WHERE deleted_at IS NULL"
        params = []
        if building_id:
            q += " AND building_id = ?"
            params.append(building_id)
        q += " ORDER BY block_number ASC"
        return dicts_from_rows(conn.execute(q, params).fetchall())

@router.get("/floors")
def list_floors(block_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        q = "SELECT * FROM floors WHERE deleted_at IS NULL"
        params = []
        if block_id:
            q += " AND block_id = ?"
            params.append(block_id)
        q += " ORDER BY floor_number ASC"
        return dicts_from_rows(conn.execute(q, params).fetchall())

@router.get("/floors/{floor_id}/grid")
def floor_grid_view(floor_id: int, current_user: dict = Depends(get_current_user)):
    grid = get_floor_grid(floor_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Qavat topilmadi")
    return grid

@router.get("/rooms")
def list_rooms(building_id: Optional[int] = None,
               block_id: Optional[int] = None,
               floor_id: Optional[int] = None,
               search: Optional[str] = None,
               status_filter: Optional[str] = None,
               limit: int = 100,
               offset: int = 0,
               current_user: dict = Depends(get_current_user)):
    # If manager, enforce assigned building
    if current_user.get("role_name") == "manager" and current_user.get("assigned_building_id"):
        building_id = current_user.get("assigned_building_id")
        
    return get_rooms(building_id, block_id, floor_id, search, status_filter, limit, offset)

@router.get("/rooms/{room_id}")
def room_detail(room_id: int, current_user: dict = Depends(get_current_user)):
    res = get_room_details(room_id)
    if not res:
        raise HTTPException(status_code=404, detail="Xona topilmadi")
    return res

@router.post("/rooms")
def create_room(req: RoomCreate, current_user: dict = Depends(require_not_observer)):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO rooms (building_id, block_id, floor_id, room_number, room_type, capacity, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (req.building_id, req.block_id, req.floor_id, req.room_number, req.room_type, req.capacity, req.notes))
        room_id = cursor.lastrowid
        
        # Automatically generate bed slots
        for bed_num in range(1, req.capacity + 1):
            conn.execute("""
                INSERT INTO room_beds (room_id, bed_number, status)
                VALUES (?, ?, 'vacant')
            """, (room_id, bed_num))
            
    log_audit("room_create", "room", room_id, None, req.dict(), f"Yangi {req.room_number}-xona yaratildi ({req.capacity} o'rin)",
              current_user['id'], current_user['full_name'])
    return {"id": room_id, "message": "Xona va uning o'rinlari muvaffaqiyatli yaratildi"}
