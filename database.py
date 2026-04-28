# database.py
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "medibook.db"

@contextmanager
def get_db():
    """Context manager for database connections - المصدر الوحيد"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # للوصول بالأسماء
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """إنشاء جميع الجداول المطلوبة - تستدعى مرة واحدة عند بدء التشغيل"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT CHECK(role IN ('doctor', 'patient', 'manager')) NOT NULL,
                specialty TEXT,
                image TEXT,
                isSuspended INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                clinic_affiliations TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # جدول العيادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinics (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                phone TEXT,
                image TEXT,
                rating REAL DEFAULT 0,
                departments TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # جدول المواعيد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                clinic_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                type TEXT CHECK(type IN ('consultation', 'follow_up')) NOT NULL,
                status TEXT CHECK(status IN ('pending', 'confirmed', 'cancelled', 'completed', 'delayed')) DEFAULT 'pending',
                price REAL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 30,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES users(_id),
                FOREIGN KEY (doctor_id) REFERENCES users(_id),
                FOREIGN KEY (clinic_id) REFERENCES clinics(_id)
            )
        ''')
        
        # جدول الفتحات المتاحة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slots (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                clinic_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 30,
                type TEXT CHECK(type IN ('consultation', 'follow_up')) NOT NULL,
                price REAL DEFAULT 0,
                status TEXT CHECK(status IN ('available', 'booked', 'unavailable')) DEFAULT 'available',
                appointment_id INTEGER,
                is_manual INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (doctor_id) REFERENCES users(_id),
                FOREIGN KEY (clinic_id) REFERENCES clinics(_id),
                UNIQUE(doctor_id, clinic_id, date, start_time)
            )
        ''')
        
        # جدول التقييمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_id INTEGER NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5) NOT NULL,
                comment TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES users(_id),
                FOREIGN KEY (doctor_id) REFERENCES users(_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments(_id),
                UNIQUE(appointment_id)
            )
        ''')
        
        # جدول متابعة الحالات (VIP)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS FollowUp_History (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                last_diagnosis TEXT,
                last_severity INTEGER DEFAULT 5,
                medications TEXT,
                last_symptoms TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES users(_id)
            )
        ''')
        
        # إنشاء الفهارس
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_followup_patient ON FollowUp_History(patient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_slots_doctor_date ON slots(doctor_id, date, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_doctor ON reviews(doctor_id)')
        
        print("✅ SQLite database initialized successfully")