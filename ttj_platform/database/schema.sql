-- ============================================================================
-- TALABALAR TURAR JOYI (TTJ) BOSHQARUV TIZIMI — DATABASE SCHEMA (SQLite 3)
-- ============================================================================
PRAGMA foreign_keys = ON;

-- 1. ROLES
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL, -- 'super_admin', 'manager', 'observer'
    display_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    assigned_building_id INTEGER REFERENCES buildings(id) ON DELETE SET NULL,
    assigned_block_id INTEGER REFERENCES blocks(id) ON DELETE SET NULL,
    assigned_floor_id INTEGER REFERENCES floors(id) ON DELETE SET NULL,
    is_active INTEGER DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. BUILDINGS (Bino)
CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    number TEXT NOT NULL,
    address TEXT,
    total_floors INTEGER DEFAULT 1,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 4. BLOCKS (Blok)
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    block_number TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 5. FLOORS (Qavat)
CREATE TABLE IF NOT EXISTS floors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id INTEGER NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    floor_number INTEGER NOT NULL,
    total_rooms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    UNIQUE(block_id, floor_number)
);

-- 6. ROOMS (Xona)
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    block_id INTEGER NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    floor_id INTEGER NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    room_number TEXT NOT NULL,
    room_type TEXT DEFAULT 'oddiy', -- 'oddiy', 'lyuks', 'ogil_bolalar', 'qizlar'
    capacity INTEGER NOT NULL DEFAULT 4,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    UNIQUE(floor_id, room_number)
);

-- 7. ROOM BEDS (Xona o'rinlari - poyezd bileti uslubidagi o'rinlar)
CREATE TABLE IF NOT EXISTS room_beds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    bed_number INTEGER NOT NULL,
    status TEXT DEFAULT 'vacant', -- 'vacant', 'occupied', 'reserved', 'maintenance'
    current_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(room_id, bed_number)
);

-- 8. SPORTS
CREATE TABLE IF NOT EXISTS sports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- 9. STUDENT PRIVILEGES (Imtiyozlar)
CREATE TABLE IF NOT EXISTS student_privileges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    discount_percentage REAL DEFAULT 0.0,
    notes TEXT
);

-- 10. STUDENTS (Talabalar)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    jshshir TEXT UNIQUE NOT NULL,
    faculty TEXT NOT NULL,
    course INTEGER NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    gender TEXT NOT NULL, -- 'Erkak', 'Ayol'
    birth_date TEXT,
    sport_id INTEGER REFERENCES sports(id) ON DELETE SET NULL,
    other_interests TEXT,
    privilege_id INTEGER REFERENCES student_privileges(id) ON DELETE SET NULL,
    total_fee REAL DEFAULT 2400000.0,
    paid_fee REAL DEFAULT 0.0,
    remaining_fee REAL DEFAULT 2400000.0,
    payment_status TEXT DEFAULT 'unpaid', -- 'paid', 'partial', 'unpaid'
    status TEXT DEFAULT 'active', -- 'active', 'moved', 'vacated', 'graduated', 'academic_leave', 'other'
    current_room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    current_bed_id INTEGER REFERENCES room_beds(id) ON DELETE SET NULL,
    check_in_date TEXT,
    check_out_date TEXT,
    vacate_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 11. STUDENT ACCOMMODATION HISTORY (Joylashish va ko'chirish tarixi)
CREATE TABLE IF NOT EXISTS student_accommodation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    bed_id INTEGER NOT NULL REFERENCES room_beds(id) ON DELETE CASCADE,
    check_in_date TEXT NOT NULL,
    check_out_date TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'moved', 'vacated'
    reason TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. PAYMENTS (To'lovlar)
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL, -- 'Naqd', 'Plastik karta', 'Payme/Click', 'Bank o\'tkazmasi'
    receipt_number TEXT,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. AUDIT LOGS (Tizim audit jurnali)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name TEXT,
    action TEXT NOT NULL, -- 'student_create', 'student_update', 'student_vacate', 'room_transfer', 'payment_create', 'import_docx', 'import_xlsx', 'user_login', etc.
    entity_type TEXT NOT NULL, -- 'student', 'room', 'payment', 'user', 'import'
    entity_id INTEGER,
    old_values TEXT, -- JSON format
    new_values TEXT, -- JSON format
    reason TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. IMPORTS (Fayl importlari tarixi)
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL, -- 'docx', 'xlsx', 'csv'
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name TEXT,
    total_rows INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed', -- 'completed', 'partial', 'failed'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. IMPORT ERRORS (Import xatoliklari jurnali)
CREATE TABLE IF NOT EXISTS import_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    student_name TEXT,
    jshshir TEXT,
    error_message TEXT NOT NULL,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. STUDENT CHANGE HISTORY (Talaba bo'yicha maydonlar o'zgarish tarixi)
CREATE TABLE IF NOT EXISTS student_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name TEXT,
    action_type TEXT NOT NULL, -- 'edit', 'move', 'vacate', 'payment'
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES for lightning-fast performance
CREATE INDEX IF NOT EXISTS idx_students_jshshir ON students(jshshir);
CREATE INDEX IF NOT EXISTS idx_students_room_id ON students(current_room_id);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_faculty ON students(faculty);
CREATE INDEX IF NOT EXISTS idx_students_course ON students(course);
CREATE INDEX IF NOT EXISTS idx_room_beds_room_id ON room_beds(room_id);
CREATE INDEX IF NOT EXISTS idx_room_beds_status ON room_beds(status);
CREATE INDEX IF NOT EXISTS idx_rooms_floor_id ON rooms(floor_id);
CREATE INDEX IF NOT EXISTS idx_rooms_building_id ON rooms(building_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_payments_student_id ON payments(student_id);
