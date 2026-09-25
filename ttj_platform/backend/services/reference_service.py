from backend.models.database import get_db, dicts_from_rows

def get_reference_data():
    with get_db() as conn:
        sports = dicts_from_rows(conn.execute("SELECT * FROM sports ORDER BY id ASC").fetchall())
        privileges = dicts_from_rows(conn.execute("SELECT * FROM student_privileges ORDER BY id ASC").fetchall())
        roles = dicts_from_rows(conn.execute("SELECT id, name, display_name, description FROM roles ORDER BY id ASC").fetchall())
        faculties = [
            "Davolash fakulteti",
            "Pediatriya fakulteti",
            "Stomatologiya fakulteti",
            "Tibbiy profilaktika va jamoat salomatligi",
            "Farmatsiya fakulteti",
            "Xalq tabobati",
            "Oliy hamshiralik ishi",
            "Harbiy tibbiyot fakulteti"
        ]
        return {
            "sports": sports,
            "privileges": privileges,
            "roles": roles,
            "faculties": faculties,
            "courses": [1, 2, 3, 4, 5, 6],
            "genders": ["Erkak", "Ayol"],
            "student_statuses": [
                {"code": "active", "name": "Faol yashovchi"},
                {"code": "moved", "name": "Ko'chirilgan"},
                {"code": "vacated", "name": "TTJdan chiqarilgan"},
                {"code": "graduated", "name": "O'qishni tugatgan"},
                {"code": "academic_leave", "name": "Akademik ta'tilda"},
                {"code": "other", "name": "Boshqa"}
            ],
            "payment_methods": ["Naqd", "Plastik karta", "Payme/Click", "Bank o'tkazmasi"]
        }
