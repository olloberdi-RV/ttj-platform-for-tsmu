import sys
import os
import random
import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ttj_platform.backend.models.database import get_db, init_db
from ttj_platform.backend.auth.security import hash_password, generate_salt, mask_jshshir

def seed_data():
    print("Initializing database schema...")
    init_db()
    
    with get_db() as conn:
        print("Seeding roles...")
        roles = [
            ("super_admin", "Super Admin", "Barcha bino, talabalar, to'lovlar va sozlamalarni to'liq boshqarish"),
            ("manager", "TTJ mas'ul xodimi", "Biriktirilgan bino va qavatlardagi xonalar va talabalarni boshqarish"),
            ("observer", "Kuzatuvchi", "Faqat ko'rish huquqi, tahrirlash va o'chirish taqiqlangan")
        ]
        conn.executemany("INSERT OR IGNORE INTO roles (name, display_name, description) VALUES (?, ?, ?)", roles)
        
        print("Seeding sports...")
        sports = [
            ("Futbol",), ("Voleybol",), ("Shaxmat",), ("Basketbol",),
            ("Stol tennisi",), ("Suzish",), ("Kurash",), ("Gimnastika",), ("Yengil atletika",)
        ]
        conn.executemany("INSERT OR IGNORE INTO sports (name) VALUES (?)", sports)
        
        print("Seeding student privileges...")
        privileges = [
            ("YETIM", "Yetimlik maqomi", 100.0, "To'liq bepul yotoqxona bilan ta'minlanadi"),
            ("BOQUVCHISIZ", "Boquvchisini yo'qotgan", 50.0, "50 foiz to'lov chegirmasi"),
            ("TEMIR_DAFTAR", "Temir daftar", 50.0, "Ijtimoiy himoya reyestri"),
            ("AYOLLAR_DAFTARI", "Ayollar daftari", 50.0, "Ijtimoiy himoyaga muhtoj oila"),
            ("NOGIRONLIK", "Nogironlik guruhi mavjud", 100.0, "1- va 2-guruh nogironligi"),
            ("IQTIDORLI", "Iqtidorli talaba (Stipendiat)", 25.0, "Nomdor davlat stipendiyasi sohibi"),
            ("ODDIY", "Oddiy / Imtiyozsiz", 0.0, "Umumiy asosda to'lov")
        ]
        conn.executemany("INSERT OR IGNORE INTO student_privileges (code, name, discount_percentage, notes) VALUES (?, ?, ?, ?)", privileges)

        print("Seeding 3 Buildings, Blocks, Floors, Rooms, and Beds...")
        # 1. Building 1: TTJ-1 (Toshkent Davolash binosi)
        cursor = conn.execute("""
            INSERT INTO buildings (name, number, address, total_floors, notes)
            VALUES ('TTJ-1 Bosh Bino', '1-bino', 'Toshkent sh., Shifokorlar ko''chasi, 2-uy', 4, 'Davolash va Pediatriya talabalari uchun')
        """)
        b1_id = cursor.lastrowid
        
        # 2. Building 2: TTJ-2 (Stomatologiya va Farmatsiya)
        cursor = conn.execute("""
            INSERT INTO buildings (name, number, address, total_floors, notes)
            VALUES ('TTJ-2 Klinika Binosi', '2-bino', 'Toshkent sh., Farobiy ko''chasi, 14-uy', 4, 'Stomatologiya va Farmatsiya fakultetlari')
        """)
        b2_id = cursor.lastrowid
        
        # 3. Building 3: TTJ-3 (Magistratura va Xalqaro talabalar)
        cursor = conn.execute("""
            INSERT INTO buildings (name, number, address, total_floors, notes)
            VALUES ('TTJ-3 Yangi Korpus', '3-bino', 'Toshkent sh., Shifokorlar ko''chasi, 4-uy', 3, 'Magistrlar va iqtidorli talabalar yotoqxonasi')
        """)
        b3_id = cursor.lastrowid

        print("Seeding users...")
        users = [
            ("admin", "admin123", "Rustamov Jamshid Karimovich", "admin@ttj.uz", "+998901112233", 1, None),
            ("manager", "manager123", "Qodirova Zulfiya Boburovna", "manager@ttj.uz", "+998932223344", 2, b1_id), # assigned building 1
            ("observer", "observer123", "Nazarov Elyor Alisherovich", "audit@ttj.uz", "+998943334455", 3, None)
        ]
        for username, pwd, full_name, email, phone, role_id, b_id in users:
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if not existing:
                salt = generate_salt()
                p_hash = hash_password(pwd, salt)
                conn.execute("""
                    INSERT INTO users (username, password_hash, salt, full_name, email, phone, role_id, assigned_building_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, p_hash, salt, full_name, email, phone, role_id, b_id))

        buildings_config = [
            (b1_id, ["A blok", "B blok"], 4, 10), # 4 floors, 10 rooms per floor
            (b2_id, ["A blok", "B blok"], 3, 10), # 3 floors, 10 rooms per floor
            (b3_id, ["A blok"], 3, 10)            # 3 floors, 10 rooms per floor
        ]
        
        all_rooms_created = []
        for b_id, block_names, num_floors, rooms_per_floor in buildings_config:
            for blk_name in block_names:
                blk_num = blk_name.split()[0]
                blk_cur = conn.execute("""
                    INSERT INTO blocks (building_id, name, block_number)
                    VALUES (?, ?, ?)
                """, (b_id, blk_name, blk_num))
                blk_id = blk_cur.lastrowid
                
                for flr in range(1, num_floors + 1):
                    flr_cur = conn.execute("""
                        INSERT INTO floors (block_id, floor_number, total_rooms)
                        VALUES (?, ?, ?)
                    """, (blk_id, flr, rooms_per_floor))
                    flr_id = flr_cur.lastrowid
                    
                    for r_idx in range(1, rooms_per_floor + 1):
                        room_number = f"{flr}{r_idx:02d}" # 101..110, 201..210, etc.
                        # Capacity distribution: mostly 4-bed, some 2-bed, some 3-bed, some 6-bed
                        if r_idx in (1, 2):
                            cap = 2
                            rtype = "lyuks"
                        elif r_idx in (3, 4):
                            cap = 3
                            rtype = "oddiy"
                        elif r_idx == 10:
                            cap = 6
                            rtype = "oddiy"
                        else:
                            cap = 4
                            rtype = "oddiy"
                            
                        r_cur = conn.execute("""
                            INSERT INTO rooms (building_id, block_id, floor_id, room_number, room_type, capacity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (b_id, blk_id, flr_id, room_number, rtype, cap))
                        r_id = r_cur.lastrowid
                        
                        bed_ids = []
                        for bed_num in range(1, cap + 1):
                            bed_cur = conn.execute("""
                                INSERT INTO room_beds (room_id, bed_number, status)
                                VALUES (?, ?, 'vacant')
                            """, (r_id, bed_num))
                            bed_ids.append((bed_cur.lastrowid, bed_num))
                            
                        all_rooms_created.append({
                            "room_id": r_id,
                            "room_number": room_number,
                            "building_id": b_id,
                            "capacity": cap,
                            "beds": bed_ids
                        })
                        
        print(f"Total rooms created: {len(all_rooms_created)}")
        
        print("Seeding 65 realistic medical students with accommodations, payments, and histories...")
        uzbek_firstnames_m = [
            "Ali", "Vali", "Jamshid", "Bekzod", "Otabek", "Jasur", "Sardor", "Farrux", "Bobur", "Sherzod",
            "Azizbek", "Ulug'bek", "Doniyor", "Doston", "Shoxrux", "Muzaffar", "Javohir", "Sanjar", "Abdurashid", "Rustam",
            "Nodirbek", "Xurshid", "Bunyod", "Akmal", "Mansur", "Islom", "Davron", "Mirjalol", "Qobil", "Asadbek"
        ]
        uzbek_lastnames_m = [
            "Aliyev", "Karimov", "Rahimov", "Tursunov", "Ismoilov", "Qodirov", "Yusupov", "Ahmedov", "Sobirov", "Nazarov",
            "Ergashev", "Murodov", "Sultonov", "Abdullayev", "Mirzayev", "G'aniyev", "Yoqubov", "Normatov", "Oripov", "Hasanov",
            "Xolmatov", "Bozorov", "Rustamov", "Zokirov", "Sharipov", "Bekmurodov", "To'rayev", "Xoliqov", "Vohidov", "Saydullayev"
        ]
        
        uzbek_firstnames_f = [
            "Nigora", "Madina", "Shahnoza", "Dildora", "Zarina", "Kamola", "Gulnoza", "Sevara", "Mohira", "Feruza",
            "Rayhona", "Dilnoza", "Umida", "Nodira", "Barno", "Shaxzoda", "Laylo", "Munira", "Saodat", "Malika"
        ]
        uzbek_lastnames_f = [
            "Karimova", "Aliyeva", "Rahimova", "Tursunova", "Ismoilova", "Qodirova", "Yusupova", "Ahmedova", "Sobirova", "Nazarova",
            "Ergasheva", "Murodova", "Sultonova", "Abdullayeva", "Mirzayeva", "G'aniyeva", "Yoqubova", "Normatova", "Oripova", "Hasanova"
        ]
        
        faculties = [
            "Davolash fakulteti", "Pediatriya fakulteti", "Stomatologiya fakulteti",
            "Farmatsiya fakulteti", "Tibbiy profilaktika va jamoat salomatligi", "Xalq tabobati"
        ]
        
        student_count = 65
        placed_students = []
        random.seed(42) # Deterministic realistic seed
        
        room_idx = 0
        for i in range(student_count):
            is_male = random.random() < 0.65
            if is_male:
                fname = random.choice(uzbek_firstnames_m)
                lname = random.choice(uzbek_lastnames_m)
                patronymic = random.choice(uzbek_firstnames_m) + " o'g'li"
                gender = "Erkak"
            else:
                fname = random.choice(uzbek_firstnames_f)
                lname = random.choice(uzbek_lastnames_f)
                patronymic = random.choice(uzbek_firstnames_m) + " qizi"
                gender = "Ayol"
                
            full_name = f"{lname} {fname} {patronymic}"
            
            # Unique 14-digit JShShIR
            prefix = "3" if is_male else "4"
            birth_year = random.randint(2001, 2006)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            dob_str = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
            jshshir = f"{prefix}{birth_day:02d}{birth_month:02d}{str(birth_year)[2:]}{random.randint(1000000, 9999999)}"
            
            faculty = random.choice(faculties)
            course = random.randint(1, 6)
            phone = f"+9989{random.choice([0,1,3,4,7,9])}{random.randint(1000000, 9999999)}"
            email = f"{fname.lower()}.{lname.lower()}{random.randint(10,99)}@med.uz"
            sport_id = random.randint(1, 8)
            privilege_id = random.choice([7, 7, 7, 1, 2, 3, 5, 6]) # 7 is normal
            
            total_fee = 2400000.0
            # Some fully paid, some partial, some unpaid
            pay_variant = random.choice(["full", "full", "partial", "partial", "unpaid"])
            if pay_variant == "full":
                paid_fee = 2400000.0
                remaining_fee = 0.0
                payment_status = "paid"
            elif pay_variant == "partial":
                paid_fee = float(random.choice([800000, 1200000, 1600000]))
                remaining_fee = total_fee - paid_fee
                payment_status = "partial"
            else:
                paid_fee = 0.0
                remaining_fee = 2400000.0
                payment_status = "unpaid"
                
            # Place in room
            target_room = all_rooms_created[room_idx % len(all_rooms_created)]
            vacant_bed = None
            for b_id, b_num in target_room["beds"]:
                cur_status = conn.execute("SELECT status FROM room_beds WHERE id = ?", (b_id,)).fetchone()["status"]
                if cur_status == "vacant":
                    vacant_bed = (b_id, b_num)
                    break
                    
            if not vacant_bed:
                room_idx += 1
                target_room = all_rooms_created[room_idx % len(all_rooms_created)]
                for b_id, b_num in target_room["beds"]:
                    cur_status = conn.execute("SELECT status FROM room_beds WHERE id = ?", (b_id,)).fetchone()["status"]
                    if cur_status == "vacant":
                        vacant_bed = (b_id, b_num)
                        break
                        
            bed_id, bed_number = vacant_bed
            check_in_date = f"2026-09-{random.randint(1, 20):02d}"
            
            s_cur = conn.execute("""
                INSERT INTO students (
                    full_name, jshshir, faculty, course, phone, email, gender, birth_date,
                    sport_id, other_interests, privilege_id, total_fee, paid_fee, remaining_fee,
                    payment_status, status, current_room_id, current_bed_id, check_in_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """, (
                full_name, jshshir, faculty, course, phone, email, gender, dob_str,
                sport_id, "Kitobxonlik, dasturlash", privilege_id, total_fee, paid_fee, remaining_fee,
                payment_status, target_room["room_id"], bed_id, check_in_date
            ))
            student_id = s_cur.lastrowid
            
            # Mark bed occupied
            conn.execute("UPDATE room_beds SET status = 'occupied', current_student_id = ? WHERE id = ?", (student_id, bed_id))
            
            # Accommodation history
            conn.execute("""
                INSERT INTO student_accommodation (student_id, room_id, bed_id, check_in_date, status, reason, created_by)
                VALUES (?, ?, ?, ?, 'active', 'O''quv yili boshida joylashtirildi', 'Administrator')
            """, (student_id, target_room["room_id"], bed_id, check_in_date))
            
            # Payments
            if paid_fee > 0:
                conn.execute("""
                    INSERT INTO payments (student_id, amount, payment_date, payment_method, receipt_number, notes, created_by)
                    VALUES (?, ?, ?, 'Plastik karta', ?, 'Yillik yotoqxona to''lovi', 'Qodirova Z.')
                """, (student_id, paid_fee, check_in_date, f"KVT-{random.randint(10000, 99999)}"))
                
            # Log creation in audit
            conn.execute("""
                INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, new_values, reason)
                VALUES (1, 'Administrator', 'student_create', 'student', ?, ?, 'Yangi talaba qabul qilindi va joylashtirildi')
            """, (student_id, f'{{"full_name": "{full_name}", "room": "{target_room["room_number"]}", "bed": {bed_number}}}'))
            
            placed_students.append((student_id, full_name, target_room["room_id"], bed_id, target_room["room_number"], bed_number))
            if (i + 1) % 3 == 0:
                room_idx += 1
                
        # Also seed 4 historical movements
        for m_idx in range(4):
            stud_tuple = placed_students[m_idx]
            conn.execute("""
                INSERT INTO student_history (student_id, field_name, old_value, new_value, user_id, user_name, action_type, reason, created_at)
                VALUES (?, 'room', '105-xona', ?, 1, 'Administrator', 'move', 'Xona qulayligi uchun almashtirildi', '2026-09-22 11:20:00')
            """, (stud_tuple[0], f"{stud_tuple[4]}-xona"))
            
        # Seed 3 vacated students with status 'vacated'
        vacated_students_data = [
            ("Boymatov Sardor Alimovich", "30504010120099", "Davolash fakulteti", 4, "+998901239876", "O'z arizasiga ko'ra ijaraga ko'chdi"),
            ("Ergasheva Munisa Akmal qizi", "40809020230088", "Pediatriya fakulteti", 6, "+998939876123", "O'qishni muvaffaqiyatli tugatdi"),
            ("Qosimov Farhod Shuhrat o'g'li", "31102030340077", "Stomatologiya fakulteti", 3, "+998945551122", "Boshqa oliygohga ko'chirildi")
        ]
        for v_name, v_jsh, v_fac, v_crs, v_ph, v_reason in vacated_students_data:
            conn.execute("""
                INSERT INTO students (
                    full_name, jshshir, faculty, course, phone, email, gender, birth_date,
                    total_fee, paid_fee, remaining_fee, payment_status, status,
                    check_in_date, check_out_date, vacate_reason
                ) VALUES (?, ?, ?, ?, ?, ?, 'Erkak', '2002-05-15', 2400000, 2400000, 0, 'paid', 'vacated',
                          '2025-09-01', '2026-06-30', ?)
            """, (v_name, v_jsh, v_fac, v_crs, v_ph, f"{v_name.split()[0].lower()}@med.uz", v_reason))
            
        print("Demo data seeded successfully!")
        
if __name__ == "__main__":
    seed_data()
