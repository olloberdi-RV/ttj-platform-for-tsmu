import sys
import os
import io
import time
import random

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from ttj_platform.backend.main import app
from ttj_platform.backend.services.import_service import generate_excel_template

client = TestClient(app)

def test_full_system():
    print("=== 1. TEST AUTHENTICATION ===")
    # 1.1 Login as admin
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "token" in data
    admin_token = data["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("Admin login: OK")
    
    # 1.2 Login as manager
    resp = client.post("/api/auth/login", json={"username": "manager", "password": "manager123"})
    assert resp.status_code == 200
    manager_token = resp.json()["token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    print("Manager login: OK")
    
    # 1.3 Invalid login check
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert resp.status_code == 400
    print("Invalid login rejection: OK")
    
    print("\n=== 2. TEST DASHBOARD & STATS ===")
    resp = client.get("/api/dashboard/stats", headers=admin_headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["counts"]["buildings"] == 3
    assert stats["counts"]["rooms"] > 0
    assert stats["counts"]["active_students"] > 0
    assert "charts" in stats
    print(f"Dashboard stats: {stats['counts']['active_students']} students, {stats['counts']['occupancy_rate']}% occupancy: OK")
    
    print("\n=== 3. TEST BUILDING HIERARCHY & ROOMS ===")
    resp = client.get("/api/buildings/hierarchy", headers=admin_headers)
    assert resp.status_code == 200
    hierarchy = resp.json()
    assert len(hierarchy) == 3
    print(f"Buildings hierarchy ({len(hierarchy)} buildings): OK")
    
    # Get room details with train-seat style beds
    resp = client.get("/api/rooms", headers=admin_headers)
    assert resp.status_code == 200
    rooms = resp.json()["items"]
    first_room_id = rooms[0]["id"]
    
    resp = client.get(f"/api/rooms/{first_room_id}", headers=admin_headers)
    assert resp.status_code == 200
    r_detail = resp.json()
    assert "beds" in r_detail
    assert len(r_detail["beds"]) == r_detail["capacity"]
    print(f"Room {r_detail['room_number']} with {len(r_detail['beds'])} beds: OK")
    
    print("\n=== 4. TEST STUDENTS SEARCH & JSHSHIR PRIVACY ===")
    resp = client.get("/api/students", headers=admin_headers)
    assert resp.status_code == 200
    students_data = resp.json()
    assert students_data["total"] > 0
    print(f"Total students found: {students_data['total']}: OK")
    
    # Search student by name
    sample_stud = students_data["items"][0]
    search_query = sample_stud["full_name"].split()[0]
    resp = client.get(f"/api/students?search={search_query}", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) > 0
    print(f"Search by query '{search_query}': OK")
    
    print("\n=== 5. TEST STUDENT CREATION & DUPLICATE PREVENTION ===")
    # Find a room with a vacant bed
    target_room = None
    target_bed_num = None
    for r in rooms:
        if r["vacant_count"] > 0:
            rd = client.get(f"/api/rooms/{r['id']}", headers=admin_headers).json()
            for b in rd["beds"]:
                if b["status"] == "vacant":
                    target_room = rd
                    target_bed_num = b["bed_number"]
                    break
        if target_room:
            break
            
    assert target_room is not None
    new_stud_jshshir = f"3{int(time.time())}{random.randint(1000, 9999)}"[:14]
    new_student_payload = {
        "full_name": "Test Alimov Botirbek Xushnud o'g'li",
        "jshshir": new_stud_jshshir,
        "faculty": "Davolash fakulteti",
        "course": 2,
        "phone": "+998909998877",
        "email": "botir.alimov@med.uz",
        "gender": "Erkak",
        "birth_date": "2004-06-15",
        "sport_id": 1,
        "privilege_id": 7,
        "total_fee": 2400000.0,
        "paid_fee": 1200000.0,
        "building_id": target_room["building_id"],
        "block_id": target_room["block_id"],
        "floor_id": target_room["floor_id"],
        "room_id": target_room["id"],
        "bed_number": target_bed_num
    }
    resp = client.post("/api/students", json=new_student_payload, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    created_id = resp.json()["student_id"]
    print(f"Student created with ID {created_id}: OK")
    
    # Duplicate JShShIR check
    resp = client.post("/api/students", json=new_student_payload, headers=admin_headers)
    assert resp.status_code == 400
    assert "allaqachon mavjud" in resp.json()["detail"]
    print("Duplicate JShShIR prevention: OK")
    
    print("\n=== 6. TEST STUDENT ROOM TRANSFER (Xonani almashtirish) ===")
    # Find another vacant bed
    another_room = None
    another_bed_num = None
    for r in rooms:
        if r["id"] != target_room["id"] and r["vacant_count"] > 0:
            rd = client.get(f"/api/rooms/{r['id']}", headers=admin_headers).json()
            for b in rd["beds"]:
                if b["status"] == "vacant":
                    another_room = rd
                    another_bed_num = b["bed_number"]
                    break
        if another_room:
            break
            
    assert another_room is not None
    move_payload = {
        "target_building_id": another_room["building_id"],
        "target_block_id": another_room["block_id"],
        "target_floor_id": another_room["floor_id"],
        "target_room_id": another_room["id"],
        "target_bed_number": another_bed_num,
        "reason": "1-kursdan 2-kursga o'tgani sababli xonasi ko'chirildi"
    }
    resp = client.post(f"/api/students/{created_id}/move", json=move_payload, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    print(f"Student room transfer to room {another_room['room_number']}: OK")
    
    # Verify history
    resp = client.get(f"/api/students/{created_id}/history", headers=admin_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) > 0
    assert any(h["action_type"] == "move" for h in history)
    print("Student change history verification: OK")
    
    print("\n=== 7. TEST PAYMENTS RECORDING ===")
    pay_payload = {
        "student_id": created_id,
        "amount": 1200000.0,
        "payment_date": "2026-09-25",
        "payment_method": "Payme/Click",
        "receipt_number": "PAY-99988",
        "notes": "Qolgan 50% to'lov"
    }
    resp = client.post("/api/payments", json=pay_payload, headers=admin_headers)
    assert resp.status_code == 200
    pay_res = resp.json()
    assert pay_res["new_remaining"] == 0.0
    assert pay_res["payment_status"] == "paid"
    print("Payment recorded and remaining fee calculated to 0.0 (Status: paid): OK")
    
    print("\n=== 8. TEST DISCHARGE / VACATE STUDENT (TTJdan chiqarish) ===")
    vacate_payload = {
        "status": "vacated",
        "reason": "O'z arizasiga binoan ijaraga chiqdi",
        "check_out_date": "2026-09-25"
    }
    resp = client.post(f"/api/students/{created_id}/vacate", json=vacate_payload, headers=admin_headers)
    assert resp.status_code == 200
    print("Student vacate: OK")
    
    # Check that the student's room bed is now vacant again!
    rd_after = client.get(f"/api/rooms/{another_room['id']}", headers=admin_headers).json()
    bed_rechecked = next(b for b in rd_after["beds"] if b["bed_number"] == another_bed_num)
    assert bed_rechecked["status"] == "vacant"
    print("Bed automatically freed upon discharge: OK")
    
    print("\n=== 9. TEST EXCEL IMPORT VALIDATION & TEMPLATES ===")
    excel_bytes = generate_excel_template()
    files = {"file": ("test_import.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = client.post("/api/import/validate", files=files, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    import_val = resp.json()
    assert import_val["total_rows"] > 0
    print(f"Import validation on Excel template: {import_val['valid_count']} valid, {import_val['error_count']} errors: OK")
    
    print("\n=== 10. TEST REPORTS & EXPORTS (PDF, Excel, CSV) ===")
    for r_type in ["all_students", "rooms_list", "debtors", "vacant_beds"]:
        resp_csv = client.get(f"/api/reports/{r_type}/export?format=csv", headers=admin_headers)
        assert resp_csv.status_code == 200
        assert len(resp_csv.content) > 0
        
        resp_xls = client.get(f"/api/reports/{r_type}/export?format=excel", headers=admin_headers)
        assert resp_xls.status_code == 200
        assert len(resp_xls.content) > 0
        
        resp_pdf = client.get(f"/api/reports/{r_type}/export?format=pdf", headers=admin_headers)
        assert resp_pdf.status_code == 200
        assert len(resp_pdf.content) > 0
        print(f"Report '{r_type}' exports (CSV, Excel, PDF): OK")
        
    print("\n=== 11. TEST AUDIT LOGS ===")
    resp = client.get("/api/audit-logs", headers=admin_headers)
    assert resp.status_code == 200
    audit_data = resp.json()
    assert audit_data["total"] > 0
    print(f"Audit logs count: {audit_data['total']}: OK")
    
    print("\n=== 12. TEST DATABASE BACKUP DOWNLOAD ===")
    resp = client.get("/api/backup/download", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.content) > 0
    print("Database JSON backup download: OK")
    
    print("\nALL SYSTEM BACKEND & BUSINESS LOGIC TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_system()
