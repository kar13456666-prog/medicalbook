from flask import Flask, request, jsonify
from flask_cors import CORS
<<<<<<< HEAD
import sqlite3
from contextlib import closing
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import traceback

app = Flask(__name__)

# ────────────────────────────────────────────────
# CORS Configuration – شامل لكل الـ routes
# ────────────────────────────────────────────────
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:4200",
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
        ],
=======
from database import init_database
import traceback
import logging

# استيراد الـ Blueprints
from routes import (
    auth_bp, doctors_bp, clinics_bp, appointments_bp,
    reviews_bp, ai_bp, analytics_bp, slots_bp
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== CORS Configuration ==========
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
>>>>>>> master
        "expose_headers": ["Content-Disposition"],
        "supports_credentials": True,
        "max_age": 86400,
    },
<<<<<<< HEAD
    # ✅ ADD THIS - Allow all routes including /chat and /health
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:4200",
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
        ],
=======
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
>>>>>>> master
        "supports_credentials": True,
    }
})

<<<<<<< HEAD
# ✅ IMPROVED: Handle OPTIONS for ALL routes
@app.before_request
def handle_options_request():
    if request.method == "OPTIONS":
        response = app.make_response("")
        origin = request.headers.get("Origin", "http://localhost:5173")
=======
# ========== CORS Middleware ==========
@app.before_request
def handle_options_request():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = app.make_response("")
        origin = request.headers.get("Origin", "")
>>>>>>> master
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        response.headers["Access-Control-Max-Age"] = "86400"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 204

<<<<<<< HEAD
# ✅ ADD THIS - Add CORS headers to every response
@app.after_request
def add_cors_headers(response):
    """Ensure CORS headers are present on all responses"""
    origin = request.headers.get("Origin")
    if origin in ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ────────────────────────────────────────────────
#                   MongoDB Connection
# ────────────────────────────────────────────────
import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import json
from typing import Optional, List, Dict, Any

# ────────────────────────────────────────────────
# SQLite Database Manager
# ────────────────────────────────────────────────

DATABASE_PATH = "medibook.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
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
    """إنشاء جميع الجداول المطلوبة"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. جدول المستخدمين (users)
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
                clinic_affiliations TEXT,  -- JSON string
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 2. جدول العيادات (clinics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinics (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                phone TEXT,
                image TEXT,
                rating REAL DEFAULT 0,
                departments TEXT,  -- JSON array
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 3. جدول المواعيد (appointments)
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
        
        # 4. جدول الفتحات المتاحة (slots)
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
        
        # 5. جدول التقييمات (reviews)
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
                # 6. جدول متابعة الحالات (FollowUp_History) - مهم للـ VIP Chat
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
        
        # إنشاء فهرس للسرعة
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_followup_patient ON FollowUp_History(patient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_followup_timestamp ON FollowUp_History(timestamp DESC)')
        
        # إنشاء الفهارس (indexes) للسرعة
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_slots_doctor_date ON slots(doctor_id, date, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_doctor ON reviews(doctor_id)')
        
        print("✅ SQLite database initialized successfully")

# استدعاء التهيئة عند بدء التشغيل
init_database()
# ────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────
# عدّل هذه الدوال كالتالي:

def convert_id(doc):
    """تحويل SQLite row إلى dict (بدون ObjectId)"""
    if isinstance(doc, dict):
        return doc
    elif isinstance(doc, sqlite3.Row):
        return {k: doc[k] for k in doc.keys()}
    return doc

# احذف convert_objectid تماماً واستخدم convert_id

def serialize_datetime(obj):
    """تحويل datetime إلى string للتخزين"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def json_to_dict(json_str):
    """تحويل JSON string إلى dict/list"""
    if json_str and isinstance(json_str, str):
        try:
            return json.loads(json_str)
        except:
            return {}
    return json_str or {}

def dict_to_json(obj):
    """تحويل dict/list إلى JSON string للتخزين"""
    if isinstance(obj, (dict, list)):
        return json.dumps(obj, default=serialize_datetime)
    return obj
def generate_slots_for_day(
    doctor_id: int,  # int بدلاً من str
    clinic_id: int,  # int بدلاً من str
    date_str: str,
    start_str: str = "09:00",
    end_str: str = "17:00",
    slot_durations: dict = None,
    prices: dict = None
):
    if slot_durations is None:
        slot_durations = {"consultation": 30, "follow_up": 20, "buffer_time": 10}
    if prices is None:
        prices = {"consultation": 0, "follow_up": 0}

    slots = []
    try:
        day_start = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
        day_end   = datetime.strptime(f"{date_str} {end_str}",   "%Y-%m-%d %H:%M")

        current = day_start
        slot_types = [
            ("consultation", slot_durations["consultation"], prices["consultation"]),
            ("follow_up",    slot_durations["follow_up"],    prices["follow_up"])
        ]

        with get_db() as conn:
            cursor = conn.cursor()
            
            while current < day_end:
                for slot_type, duration, price in slot_types:
                    slot_end = current + timedelta(minutes=duration)
                    if slot_end > day_end:
                        break

                    # إضافة slot إلى قاعدة البيانات مباشرة
                    cursor.execute('''
                        INSERT OR IGNORE INTO slots 
                        (doctor_id, clinic_id, date, start_time, end_time, 
                         duration_minutes, type, price, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        doctor_id, clinic_id, date_str,
                        current.strftime("%H:%M"), slot_end.strftime("%H:%M"),
                        duration, slot_type, float(price), "available",
                        datetime.utcnow().isoformat(), datetime.utcnow().isoformat()
                    ))
                    
                    current += timedelta(minutes=duration + slot_durations["buffer_time"])

        return True  # نجاح

    except Exception as e:
        print(f"خطأ: {e}")
        traceback.print_exc()
        return False
    
def is_slot_available(doctor_id: int, clinic_id: int, date_str: str, start_time: str, duration_minutes: int) -> bool:
    """التحقق من توفر موعد باستخدام SQLite"""
    try:
        start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.strftime("%H:%M")
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM appointments
                WHERE doctor_id = ? 
                AND clinic_id = ? 
                AND date = ?
                AND status != 'cancelled'
                AND (
                    (start_time < ? AND end_time > ?) OR
                    (start_time >= ? AND end_time <= ?)
                )
            ''', (doctor_id, clinic_id, date_str, end_time, start_time, start_time, end_time))
            
            result = cursor.fetchone()
            return result["count"] == 0
            
    except Exception as e:
        print(f"خطأ: {e}")
        return False

# ────────────────────────────────────────────────
# Auth Routes
# ────────────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        required = ["name", "email", "password", "role"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        # التحقق من عدم وجود الإيميل باستخدام SQLite
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT _id FROM users WHERE email = ?", (data["email"],))
            if cursor.fetchone():
                return jsonify({"error": "Email already registered"}), 409

            # تحضير بيانات المستخدم
            now_iso = datetime.now(timezone.utc).isoformat()
            
            doc = {
                "name": data["name"].strip(),
                "email": data["email"].strip().lower(),
                "password": generate_password_hash(data["password"]),
                "role": data["role"],
                "created_at": now_iso,
                "updated_at": now_iso,
            }

            if data["role"] == "doctor":
                doc.update({
                    "specialty": data.get("specialty", ""),
                    "image": data.get("image", "https://i.pravatar.cc/150"),
                    "isSuspended": 0,  # 0 = False, 1 = True
                    "rating": 0.0,
                    "rating_count": 0,
                    "clinic_affiliations": "[]"  # JSON string
                })
            else:
                # للمريض أو المدير
                doc.update({
                    "specialty": None,
                    "image": data.get("image", "https://i.pravatar.cc/150"),
                    "isSuspended": 0,
                    "rating": 0.0,
                    "rating_count": 0,
                    "clinic_affiliations": "[]"
                })

            # إدراج المستخدم
            columns = ', '.join(doc.keys())
            placeholders = ', '.join(['?'] * len(doc))
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, list(doc.values()))
            user_id = cursor.lastrowid

        return jsonify({"message": "User created", "id": user_id}), 201

    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        # 1. توحيد الإيميل المدخل (حروف صغيرة وبدون مسافات)
        email_input = data.get("email", "").strip().lower()
        password_input = data.get("password")

        if not email_input or not password_input:
            return jsonify({"error": "Email and password required"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            # البحث باستخدام الإيميل الموحد
            cursor.execute("SELECT * FROM users WHERE email = ?", (email_input,))
            user = cursor.fetchone()

            if not user:
                return jsonify({"error": "Invalid credentials"}), 401
            
            # بقية الكود...
            # التحقق من كلمة المرور
            if not check_password_hash(user["password"], data.get("password")):
                return jsonify({"error": "Invalid credentials"}), 401

            # تحويل user من sqlite3.Row إلى dict
            user_dict = dict(user)
            
            # تجهيز بيانات المستخدم للرد
            user_data = {
                "id": user_dict["_id"],
                "name": user_dict["name"],
                "email": user_dict["email"],
                "role": user_dict["role"],
            }

            if user_dict["role"] == "doctor":
                user_data.update({
                    "specialty": user_dict.get("specialty"),
                    "isSuspended": bool(user_dict.get("isSuspended", 0)),
                })

            return jsonify({"user": user_data}), 200
        

    except Exception as e:
        print(f"Error in login: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    print(f"DEBUG: Found user in DB: {user}")

# ────────────────────────────────────────────────
# Manager → Doctors & Clinics CRUD
# ────────────────────────────────────────────────
@app.route('/api/manager/doctors', methods=['GET'])
def get_all_doctors():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE role = 'doctor'")
            doctors = cursor.fetchall()
            
            cleaned = []
            for doc in doctors:
                doc_dict = dict(doc)
                doc_dict["id"] = doc_dict.pop("_id")
                
                # تحويل JSON strings إلى lists/dicts
                if doc_dict.get("clinic_affiliations"):
                    try:
                        doc_dict["clinic_affiliations"] = json.loads(doc_dict["clinic_affiliations"])
                    except:
                        doc_dict["clinic_affiliations"] = []
                else:
                    doc_dict["clinic_affiliations"] = []
                
                # تحويل boolean
                doc_dict["isSuspended"] = bool(doc_dict.get("isSuspended", 0))
                
                cleaned.append(doc_dict)
            
            return jsonify(cleaned), 200
            
    except Exception as e:
        print(f"Error in get_all_doctors: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
# أضف هذا الـ endpoint في ملف app.py

@app.route('/api/manager/doctor/<int:doctor_id>', methods=['GET'])
def get_doctor_by_id(doctor_id):
    """جلب بيانات دكتور واحد بالـ ID"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id,))
            doctor = cursor.fetchone()
            
            if not doctor:
                return jsonify({"error": "Doctor not found"}), 404
            
            doctor_dict = dict(doctor)
            doctor_dict["id"] = doctor_dict.pop("_id")
            
            # تحويل JSON strings
            if doctor_dict.get("clinic_affiliations"):
                try:
                    doctor_dict["clinic_affiliations"] = json.loads(doctor_dict["clinic_affiliations"])
                except:
                    doctor_dict["clinic_affiliations"] = []
            else:
                doctor_dict["clinic_affiliations"] = []
            
            doctor_dict["isSuspended"] = bool(doctor_dict.get("isSuspended", 0))
            
            # تحويل التواريخ
            if doctor_dict.get("created_at"):
                doctor_dict["created_at"] = doctor_dict["created_at"]
            if doctor_dict.get("updated_at"):
                doctor_dict["updated_at"] = doctor_dict["updated_at"]
            
            return jsonify(doctor_dict), 200
            
    except Exception as e:
        print(f"Error in get_doctor_by_id: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/add-doctor', methods=['POST'])
def add_doctor():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        # الحقول المطلوبة الأساسية
        required_fields = ["name", "email", "password", "specialty"]
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            # التحقق من تكرار الإيميل
            cursor.execute("SELECT _id FROM users WHERE email = ?", (data["email"],))
            if cursor.fetchone():
                return jsonify({"error": "Email already exists"}), 409

            # تحضير بيانات الدكتور الأساسية
            hashed_password = generate_password_hash(data["password"])
            now_iso = datetime.utcnow().isoformat()
            
            new_doctor = {
                "name": data["name"].strip(),
                "email": data["email"].strip().lower(),
                "password": hashed_password,
                "role": "doctor",
                "specialty": data["specialty"].strip(),
                "image": data.get("image", ""),
                "isSuspended": 0,  # False
                "rating": 0,
                "rating_count": 0,
                "created_at": now_iso,
                "updated_at": now_iso,
                "clinic_affiliations": "[]"  # JSON string
            }

            # إضافة الارتباط بالعيادة (إذا تم إرسال clinic_id)
            clinic_id = data.get("clinic_id")
            if clinic_id:
                try:
                    clinic_id_int = int(clinic_id)  # SQLite uses INTEGER
                except:
                    return jsonify({"error": "Invalid clinic_id format"}), 400

                # التحقق من وجود العيادة
                cursor.execute("SELECT _id FROM clinics WHERE _id = ?", (clinic_id_int,))
                if not cursor.fetchone():
                    return jsonify({"error": "Clinic not found"}), 404

                # إعدادات الـ affiliation الجديدة
                slot_duration_input = data.get("slot_duration", {})
                prices_input = data.get("prices", {})

                affiliation = {
                    "clinic_id": clinic_id_int,
                    "is_active": True,
                    "joined_at": now_iso,
                    "slot_duration": {
                        "consultation": int(slot_duration_input.get("consultation", 30)),
                        "follow_up":    int(slot_duration_input.get("follow_up", 20)),
                        "buffer_time":  int(slot_duration_input.get("buffer_time", 10))
                    },
                    "prices": {
                        "consultation": float(prices_input.get("consultation", 0)),
                        "follow_up":    float(prices_input.get("follow_up", 0))
                    },
                    "weekly_schedule": [],
                    "exceptions": []
                }
                
                # تحويل إلى JSON string
                affiliations_list = [affiliation]
                new_doctor["clinic_affiliations"] = json.dumps(affiliations_list)

            # إدراج الدكتور في قاعدة البيانات
            columns = ', '.join(new_doctor.keys())
            placeholders = ', '.join(['?'] * len(new_doctor))
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, list(new_doctor.values()))
            doctor_id = cursor.lastrowid

            return jsonify({
                "success": True,
                "message": "Doctor created successfully",
                "doctor_id": doctor_id
            }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "Server error while creating doctor",
            "detail": str(e)
        }), 500


@app.route('/api/manager/doctor/<id>', methods=['PUT'])
def update_doctor(id):
    try:
        data = request.get_json()
        print("Received PUT data:", data)

        try:
            doc_id = int(id)  # SQLite uses INTEGER
        except Exception:
            return jsonify({"error": "Invalid doctor ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            # التحقق من وجود الدكتور
            cursor.execute("SELECT * FROM users WHERE _id = ? AND role = 'doctor'", (doc_id,))
            doctor = cursor.fetchone()
            
            if not doctor:
                return jsonify({"error": "Doctor not found"}), 404

            update_fields = {}
            update_values = []
            
            if "name" in data:
                update_fields["name"] = data["name"].strip()
            if "specialty" in data:
                update_fields["specialty"] = data["specialty"].strip()
            if "image" in data and data["image"]:
                update_fields["image"] = data["image"]

            # تحديث إعدادات العيادة (أول affiliation فقط)
            if "slot_duration" in data or "prices" in data:
                # جلب الـ affiliations الحالية
                cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doc_id,))
                result = cursor.fetchone()
                affiliations = []
                
                if result and result["clinic_affiliations"]:
                    try:
                        affiliations = json.loads(result["clinic_affiliations"])
                    except:
                        affiliations = []
                
                if affiliations:
                    # تحديث أول affiliation
                    if "slot_duration" in data:
                        affiliations[0]["slot_duration"] = data["slot_duration"]
                    if "prices" in data:
                        affiliations[0]["prices"] = data["prices"]
                    
                    update_fields["clinic_affiliations"] = json.dumps(affiliations)

            if update_fields:
                update_fields["updated_at"] = datetime.utcnow().isoformat()
                
                # بناء query التحديث
                set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
                update_values = list(update_fields.values())
                update_values.append(doc_id)
                
                query = f"UPDATE users SET {set_clause} WHERE _id = ?"
                cursor.execute(query, update_values)
                
                print(f"Modified count: {cursor.rowcount}")
                if cursor.rowcount == 0:
                    print("Warning: No fields were changed – data may be identical")

            # جلب البيانات المحدثة
            cursor.execute("SELECT * FROM users WHERE _id = ?", (doc_id,))
            updated = cursor.fetchone()
            
            if updated:
                updated_dict = dict(updated)
                updated_dict["_id"] = updated_dict.pop("_id")
                
                # تحويل JSON strings
                if updated_dict.get("clinic_affiliations"):
                    try:
                        updated_dict["clinic_affiliations"] = json.loads(updated_dict["clinic_affiliations"])
                        # تحويل clinic_id من int إلى str للتأكد (اختياري)
                        for aff in updated_dict["clinic_affiliations"]:
                            if "clinic_id" in aff:
                                aff["clinic_id"] = str(aff["clinic_id"])
                    except:
                        updated_dict["clinic_affiliations"] = []
                
                updated_dict["isSuspended"] = bool(updated_dict.get("isSuspended", 0))

            return jsonify({
                "message": "Doctor updated successfully",
                "doctor": updated_dict if updated else None
            }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/doctor/<id>', methods=['DELETE'])
def delete_doctor(id):
    try:
        try:
            doc_id = int(id)  # SQLite uses INTEGER
        except Exception:
            return jsonify({"error": "Invalid doctor ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            # البحث عن الدكتور والتأكد من وجوده
            cursor.execute("SELECT _id FROM users WHERE _id = ? AND role = 'doctor'", (doc_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Doctor not found"}), 404

            # حذف جميع المواعيد المرتبطة بالدكتور
            cursor.execute("DELETE FROM appointments WHERE doctor_id = ?", (doc_id,))
            
            # حذف جميع الـ slots المرتبطة بالدكتور
            cursor.execute("DELETE FROM slots WHERE doctor_id = ?", (doc_id,))
            
            # حذف جميع التقييمات المرتبطة بالدكتور
            cursor.execute("DELETE FROM reviews WHERE doctor_id = ?", (doc_id,))
            
            # حذف الدكتور نفسه
            cursor.execute("DELETE FROM users WHERE _id = ?", (doc_id,))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Doctor could not be deleted"}), 500

        return jsonify({
            "success": True,
            "message": "Doctor and all related data deleted successfully"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Add this after your existing imports
from collections import defaultdict
from datetime import datetime, timedelta, date
import calendar
import json

# ────────────────────────────────────────────────
# Doctor Analytics Routes (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/analytics', methods=['GET'])
def get_doctor_analytics(doctor_id):
    """
    Get comprehensive analytics for a doctor including:
    - Total appointments count
    - Revenue statistics
    - Appointments by status
    - Time-based analytics (daily, weekly, monthly, yearly)
    """
    try:
        doctor_id_int = int(doctor_id)  # SQLite uses INTEGER
        
        # Get query parameters for date range
        period = request.args.get('period', 'all')  # day, week, month, year, all
        specific_date = request.args.get('date')  # YYYY-MM-DD format
        
        # Build date filter
        date_condition = ""
        date_params = []
        today = datetime.now(timezone.utc).date()
        
        if period == 'day':
            if specific_date:
                target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
            else:
                target_date = today
            date_condition = "AND date = ?"
            date_params = [target_date.strftime('%Y-%m-%d')]
            
        elif period == 'week':
            if specific_date:
                target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
            else:
                target_date = today
            # Get start of week (Monday)
            start_of_week = target_date - timedelta(days=target_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            date_condition = "AND date >= ? AND date <= ?"
            date_params = [start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')]
            
        elif period == 'month':
            if specific_date:
                target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
            else:
                target_date = today
            start_of_month = target_date.replace(day=1)
            last_day = calendar.monthrange(target_date.year, target_date.month)[1]
            end_of_month = target_date.replace(day=last_day)
            date_condition = "AND date >= ? AND date <= ?"
            date_params = [start_of_month.strftime('%Y-%m-%d'), end_of_month.strftime('%Y-%m-%d')]
            
        elif period == 'year':
            if specific_date:
                target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
            else:
                target_date = today
            start_of_year = target_date.replace(month=1, day=1)
            end_of_year = target_date.replace(month=12, day=31)
            date_condition = "AND date >= ? AND date <= ?"
            date_params = [start_of_year.strftime('%Y-%m-%d'), end_of_year.strftime('%Y-%m-%d')]

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all appointments for this doctor with optional date filter
            query = "SELECT * FROM appointments WHERE doctor_id = ?"
            params = [doctor_id_int]
            
            if date_condition:
                query += f" {date_condition}"
                params.extend(date_params)
            
            cursor.execute(query, params)
            appointments = cursor.fetchall()
            
            # Convert to list of dicts
            appointments_list = [dict(apt) for apt in appointments]
        
        # Initialize analytics object
        analytics = {
            "total_appointments": len(appointments_list),
            "appointments_by_status": defaultdict(int),
            "appointments_by_type": defaultdict(int),
            "revenue": {
                "total": 0,
                "by_status": defaultdict(float),
                "by_type": defaultdict(float)
            },
            "time_analytics": {
                "daily": defaultdict(int),
                "weekly": defaultdict(int),
                "monthly": defaultdict(int),
                "yearly": defaultdict(int)
            },
            "patient_analytics": {
                "unique_patients": set(),
                "new_patients": 0,
                "returning_patients": 0
            }
        }

        # Process each appointment
        patient_first_visit = defaultdict(bool)
        
        for apt in appointments_list:
            status = apt.get('status', 'unknown')
            apt_type = apt.get('type', 'unknown')
            price = float(apt.get('price', 0))
            apt_date = apt.get('date', '')
            patient_id = str(apt.get('patient_id', ''))
            
            # Count by status
            analytics["appointments_by_status"][status] += 1
            
            # Count by type
            analytics["appointments_by_type"][apt_type] += 1
            
            # Revenue calculations (only for completed or confirmed appointments)
            if status in ['completed', 'confirmed']:
                analytics["revenue"]["total"] += price
                analytics["revenue"]["by_status"][status] += price
                analytics["revenue"]["by_type"][apt_type] += price
            
            # Time-based analytics
            if apt_date:
                try:
                    date_obj = datetime.strptime(apt_date, '%Y-%m-%d').date()
                    
                    # Daily
                    analytics["time_analytics"]["daily"][apt_date] += 1
                    
                    # Weekly (week number)
                    week_number = date_obj.isocalendar()[1]
                    year = date_obj.year
                    week_key = f"{year}-W{week_number}"
                    analytics["time_analytics"]["weekly"][week_key] += 1
                    
                    # Monthly
                    month_key = apt_date[:7]  # YYYY-MM
                    analytics["time_analytics"]["monthly"][month_key] += 1
                    
                    # Yearly
                    year_key = str(date_obj.year)
                    analytics["time_analytics"]["yearly"][year_key] += 1
                    
                except:
                    pass
            
            # Patient analytics
            if patient_id:
                analytics["patient_analytics"]["unique_patients"].add(patient_id)
                
                # Check if this is patient's first visit to this doctor
                if not patient_first_visit[patient_id]:
                    patient_first_visit[patient_id] = True
                    
                    with get_db() as conn:
                        cursor = conn.cursor()
                        # Check if there are any older appointments
                        cursor.execute('''
                            SELECT _id FROM appointments 
                            WHERE doctor_id = ? AND patient_id = ? AND date < ?
                            LIMIT 1
                        ''', (doctor_id_int, int(patient_id), apt_date))
                        
                        older_appointment = cursor.fetchone()
                        
                        if older_appointment:
                            analytics["patient_analytics"]["returning_patients"] += 1
                        else:
                            analytics["patient_analytics"]["new_patients"] += 1

        # Convert defaultdicts to regular dicts and sets to counts
        analytics["appointments_by_status"] = dict(analytics["appointments_by_status"])
        analytics["appointments_by_type"] = dict(analytics["appointments_by_type"])
        analytics["revenue"]["by_status"] = dict(analytics["revenue"]["by_status"])
        analytics["revenue"]["by_type"] = dict(analytics["revenue"]["by_type"])
        analytics["time_analytics"]["daily"] = dict(analytics["time_analytics"]["daily"])
        analytics["time_analytics"]["weekly"] = dict(analytics["time_analytics"]["weekly"])
        analytics["time_analytics"]["monthly"] = dict(analytics["time_analytics"]["monthly"])
        analytics["time_analytics"]["yearly"] = dict(analytics["time_analytics"]["yearly"])
        analytics["patient_analytics"]["unique_patients"] = len(analytics["patient_analytics"]["unique_patients"])

        # Add completion rate
        total_non_cancelled = sum(count for status, count in analytics["appointments_by_status"].items() 
                                 if status not in ['cancelled'])
        completed = analytics["appointments_by_status"].get('completed', 0)
        analytics["completion_rate"] = round((completed / total_non_cancelled * 100) if total_non_cancelled > 0 else 0, 2)

        # Add average revenue per appointment
        analytics["average_revenue_per_appointment"] = round(
            analytics["revenue"]["total"] / analytics["total_appointments"] 
            if analytics["total_appointments"] > 0 else 0, 2
        )

        return jsonify({
            "success": True,
            "analytics": analytics
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error in doctor analytics: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/<doctor_id>/appointments/count', methods=['GET'])
def get_doctor_appointments_count(doctor_id):
    """
    Get total appointments count for a doctor
    """
    try:
        doctor_id_int = int(doctor_id)
        
        # Get optional status filter
        status = request.args.get('status')  # e.g., ?status=completed
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM appointments WHERE doctor_id = ? AND status = ?",
                    (doctor_id_int, status)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM appointments WHERE doctor_id = ?",
                    (doctor_id_int,)
                )
            
            result = cursor.fetchone()
            total_count = result["count"] if result else 0
        
        return jsonify({
            "success": True,
            "total_appointments": total_count,
            "doctor_id": doctor_id
        }), 200
        
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error in appointments count: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/<doctor_id>/appointments/stats', methods=['GET'])
def get_doctor_appointment_stats(doctor_id):
    """
    Get appointment statistics for a doctor
    """
    try:
        doctor_id_int = int(doctor_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get counts by status with revenue
            cursor.execute('''
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(CASE WHEN status IN ('completed', 'confirmed') THEN price ELSE 0 END) as revenue
                FROM appointments
                WHERE doctor_id = ?
                GROUP BY status
            ''', (doctor_id_int,))
            
            stats = cursor.fetchall()
            
            # Format the response
            result = {
                "total": 0,
                "by_status": {}
            }
            
            for item in stats:
                status = item["status"]
                count = item["count"]
                revenue = item["revenue"] or 0
                
                result["by_status"][status] = {
                    "count": count,
                    "revenue": round(float(revenue), 2)
                }
                result["total"] += count
        
        return jsonify({
            "success": True,
            "stats": result
        }), 200
        
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error in appointment stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/clinics', methods=['GET'])
def get_all_clinics():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clinics ORDER BY created_at DESC")
            clinics = cursor.fetchall()
            
            cleaned = []
            for clinic in clinics:
                clinic_dict = dict(clinic)
                clinic_dict["id"] = clinic_dict.pop("_id")
                
                # Convert departments from JSON string to list
                if clinic_dict.get("departments"):
                    try:
                        clinic_dict["departments"] = json.loads(clinic_dict["departments"])
                    except:
                        clinic_dict["departments"] = []
                else:
                    clinic_dict["departments"] = []
                
                cleaned.append(clinic_dict)
            
            return jsonify(cleaned), 200
            
    except Exception as e:
        print(f"Error in get_all_clinics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/add-clinic', methods=['POST'])
def add_clinic():
    try:
        data = request.json
        if not data.get("name"):
            return jsonify({"error": "Clinic name is required"}), 400

        now_iso = datetime.now(timezone.utc).isoformat()
        
        clinic = {
            "name": data["name"].strip(),
            "location": data.get("location", "").strip(),
            "phone": data.get("phone", "").strip(),
            "image": data.get("image", "https://images.unsplash.com/photo-1576765607925-9f0bfae3a1c6"),
            "rating": float(data.get("rating", 0.0)),
            "departments": json.dumps(data.get("departments", [])),  # Store as JSON string
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        with get_db() as conn:
            cursor = conn.cursor()
            columns = ', '.join(clinic.keys())
            placeholders = ', '.join(['?'] * len(clinic))
            query = f"INSERT INTO clinics ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, list(clinic.values()))
            clinic_id = cursor.lastrowid

        return jsonify({
            "message": "Clinic created",
            "id": clinic_id
        }), 201
        
    except Exception as e:
        print(f"Error in add_clinic: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/clinic/<id>', methods=['PUT'])
def update_clinic(id):
    try:
        data = request.json
        
        try:
            clinic_id = int(id)
        except:
            return jsonify({"error": "Invalid clinic ID format"}), 400

        update_fields = {}
        update_values = []
        allowed_fields = ["name", "location", "phone", "image", "rating", "departments"]

        for field in allowed_fields:
            if field in data:
                if field == "rating":
                    update_fields[field] = float(data[field])
                elif field == "departments":
                    update_fields[field] = json.dumps(data[field])
                else:
                    update_fields[field] = data[field].strip() if isinstance(data[field], str) else data[field]

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Build UPDATE query
            set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
            update_values = list(update_fields.values())
            update_values.append(clinic_id)
            
            cursor.execute(f"UPDATE clinics SET {set_clause} WHERE _id = ?", update_values)
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Clinic not found"}), 404

        return jsonify({"message": "Clinic updated successfully"}), 200
        
    except Exception as e:
        print(f"Error in update_clinic: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/manager/clinic/<id>', methods=['DELETE'])
def delete_clinic(id):
    try:
        try:
            clinic_id = int(id)
        except:
            return jsonify({"error": "Invalid clinic ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            # First, check if clinic exists
            cursor.execute("SELECT _id FROM clinics WHERE _id = ?", (clinic_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Clinic not found"}), 404
            
            # Delete related appointments first (foreign key constraint)
            cursor.execute("DELETE FROM appointments WHERE clinic_id = ?", (clinic_id,))
            
            # Delete related slots
            cursor.execute("DELETE FROM slots WHERE clinic_id = ?", (clinic_id,))
            
            # Delete the clinic
            cursor.execute("DELETE FROM clinics WHERE _id = ?", (clinic_id,))

        return jsonify({"message": "Clinic deleted successfully"}), 200
        
    except Exception as e:
        print(f"Error in delete_clinic: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clinics/<clinic_id>', methods=['GET'])
def get_clinic_by_id(clinic_id):
    """Get specific clinic by ID"""
    try:
        try:
            clinic_id_int = int(clinic_id)
        except:
            return jsonify({"error": "Invalid clinic ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT _id, name, location, phone, image, rating, departments, created_at, updated_at
                FROM clinics 
                WHERE _id = ?
            ''', (clinic_id_int,))
            
            clinic = cursor.fetchone()
            
            if not clinic:
                return jsonify({"error": "Clinic not found"}), 404

            # Convert to dict and process
            clinic_dict = dict(clinic)
            clinic_dict["id"] = clinic_dict.pop("_id")
            
            # Convert departments from JSON string to list
            if clinic_dict.get("departments"):
                try:
                    clinic_dict["departments"] = json.loads(clinic_dict["departments"])
                except:
                    clinic_dict["departments"] = []
            else:
                clinic_dict["departments"] = []

            return jsonify(clinic_dict), 200

    except Exception as e:
        print(f"Error fetching clinic {clinic_id}: {e}")
        return jsonify({"error": "Server error"}), 500


# ────────────────────────────────────────────────
# Doctor → Clinics & Schedule & Exceptions (SQLite)
# ────────────────────────────────────────────────
@app.route('/api/doctor/<doctor_id>/clinics', methods=['GET'])
def get_doctor_clinics(doctor_id):
    """
    Get all active clinics where doctor works
    """
    try:
        doctor_id_int = int(doctor_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get doctor's clinic affiliations
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({"error": "Doctor not found"}), 404
            
            # تحويل الـ Row إلى dict للوصول للبيانات بأمان
            doctor_data = dict(row)
            
            # Parse affiliations from JSON
            affiliations = []
            if doctor_data.get("clinic_affiliations"):
                try:
                    # تأكد من عمل import json في أول الملف
                    affiliations = json.loads(doctor_data["clinic_affiliations"])
                except Exception as e:
                    print(f"JSON Parse error: {e}")
                    affiliations = []
            
            # Extract active clinic IDs
            active_clinic_ids = []
            for aff in affiliations:
                # الـ aff هنا أصلاً dict لأن json.loads حولته
                if aff.get("is_active", True):
                    clinic_id = aff.get("clinic_id")
                    if clinic_id:
                        active_clinic_ids.append(int(clinic_id))
            
            if not active_clinic_ids:
                return jsonify([]), 200
            
            # Get clinic details
            placeholders = ','.join(['?'] * len(active_clinic_ids))
            cursor.execute(f'''
                SELECT _id, name, location, phone, image, rating 
                FROM clinics 
                WHERE _id IN ({placeholders})
            ''', active_clinic_ids)
            
            clinics_rows = cursor.fetchall()
            
            final_result = []
            for c_row in clinics_rows:
                # تحويل كل صف لـ dict عشان نستخدم .get()
                c_dict = dict(c_row)
                final_result.append({
                    "id": c_dict.get("_id"),
                    "name": c_dict.get("name", "Unknown"),
                    "location": c_dict.get("location", ""),
                    "phone": c_dict.get("phone", ""),
                    "image": c_dict.get("image", ""),
                    "rating": c_dict.get("rating", 0.0)
                })
            
            return jsonify(final_result), 200
        
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error fetching doctor clinics: {str(e)}")
        import traceback
        traceback.print_exc() # عشان تشوف الخطأ بالتفصيل في الـ terminal
        return jsonify({"error": "Server error"}), 500
@app.route('/api/appointments/book', methods=['POST'])
def book_appointment():
    try:
        data = request.json
        time_val = data.get("start_time") or data.get("time_slot")
        
        required = ["patient_id", "doctor_id", "clinic_id", "date", "type"]
        if not time_val or not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            # جلب السعر من slots أولاً
            cursor.execute('''
                SELECT price FROM slots 
                WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ? 
                LIMIT 1
            ''', (data["doctor_id"], data["clinic_id"], data["date"], time_val))
            
            slot = cursor.fetchone()
            price = float(slot["price"]) if slot and slot["price"] else 250.0  # fallback
            
            # إذا كان follow_up، خفض السعر شوية
            if data.get("type") == "follow_up":
                price = price * 0.7

            cursor.execute('''
                INSERT INTO appointments 
                (patient_id, doctor_id, clinic_id, date, start_time, end_time, type, status, price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            ''', (
                data["patient_id"], 
                data["doctor_id"], 
                data["clinic_id"], 
                data["date"], 
                time_val,
                time_val, 
                data["type"], 
                price,
                datetime.now().isoformat()
            ))
            
            appointment_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                "success": True, 
                "message": "Appointment booked successfully",
                "appointment_id": appointment_id,
                "price": price
            }), 201
            
    except Exception as e:
        print(f"❌ Booking Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/api/patient/<int:patient_id>/appointments', methods=['GET', 'OPTIONS'])
def get_patient_appointments(patient_id):
    """Get all appointments for a patient with doctor and clinic details"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    a._id,
                    a.date, 
                    a.start_time, 
                    a.end_time,
                    a.type, 
                    a.status,
                    a.price,
                    a.duration_minutes,
                    a.created_at,
                    u._id as doctor_id,
                    u.name as doctor_name,
                    u.specialty as doctor_specialty,
                    u.image as doctor_image,
                    c._id as clinic_id,
                    c.name as clinic_name,
                    c.location as clinic_location
                FROM appointments a
                LEFT JOIN users u ON a.doctor_id = u._id
                LEFT JOIN clinics c ON a.clinic_id = c._id
                WHERE a.patient_id = ?
                ORDER BY a.date DESC, a.start_time DESC
            '''
            cursor.execute(query, (patient_id,))
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                apt = dict(row)
                # Convert ID to string for frontend compatibility
                apt["_id"] = str(apt["_id"])
                if apt.get("doctor_id"):
                    apt["doctor_id"] = str(apt["doctor_id"])
                if apt.get("clinic_id"):
                    apt["clinic_id"] = str(apt["clinic_id"])
                
                # Set defaults for null values
                if not apt.get("doctor_name"):
                    apt["doctor_name"] = "Unknown"
                if not apt.get("clinic_name"):
                    apt["clinic_name"] = "Not specified"
                if not apt.get("price"):
                    apt["price"] = 0
                if not apt.get("duration_minutes"):
                    apt["duration_minutes"] = 30
                    
                appointments.append(apt)
            
            return jsonify({
                "success": True,
                "appointments": appointments,
                "total": len(appointments)
            }), 200
            
    except Exception as e:
        print(f"❌ Error in get_patient_appointments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/affiliate', methods=['POST', 'DELETE'])
def manage_clinic_affiliation(doctor_id, clinic_id):
    try:
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get current doctor data
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404
            
            # Parse existing affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []

            if request.method == 'POST':
                # Check if already affiliated
                for aff in affiliations:
                    if aff.get("clinic_id") == clinic_id_int:
                        return jsonify({"error": "Doctor already affiliated with this clinic"}), 400
                
                # Check if clinic exists
                cursor.execute("SELECT _id FROM clinics WHERE _id = ?", (clinic_id_int,))
                if not cursor.fetchone():
                    return jsonify({"error": "Clinic not found"}), 404

                data = request.json or {}
                
                # Create new affiliation
                new_affiliation = {
                    "clinic_id": clinic_id_int,
                    "weekly_schedule": [],
                    "exceptions": [],
                    "slot_duration": data.get("slot_duration", 30),
                    "is_active": True,
                    "joined_at": datetime.now(timezone.utc).isoformat()
                }
                
                affiliations.append(new_affiliation)
                
                # Update database
                cursor.execute(
                    "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                    (json.dumps(affiliations), datetime.now(timezone.utc).isoformat(), doctor_id_int)
                )
                
                return jsonify({"message": "Doctor affiliated with clinic successfully"}), 201
                
            elif request.method == 'DELETE':
                # Remove affiliation
                new_affiliations = [aff for aff in affiliations if aff.get("clinic_id") != clinic_id_int]
                
                if len(new_affiliations) == len(affiliations):
                    return jsonify({"error": "Affiliation not found"}), 404
                
                # Update database
                cursor.execute(
                    "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                    (json.dumps(new_affiliations), datetime.now(timezone.utc).isoformat(), doctor_id_int)
                )
                
                return jsonify({"message": "Affiliation removed successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error managing affiliation: {str(e)}")
        return jsonify({"error": "Server error"}), 500
# ────────────────────────────────────────────────
# Appointments & Booking (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/appointments/today', methods=['GET'])
def get_today_appointments(doctor_id):
    """
    Get today's appointments for a doctor
    - If ?clinic_id=xxx is passed → returns only that clinic's appointments
    - Without clinic_id → returns all appointments from all clinics
    """
    try:
        doctor_id_int = int(doctor_id)
        clinic_id_str = request.args.get('clinic_id')
        
        # Today's date in YYYY-MM-DD format
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Build the query
            query = '''
                SELECT 
                    a._id, a.patient_id, a.start_time, a.end_time, a.type, a.status,
                    p.name as patient_name, p.image as patient_image,
                    c._id as clinic_id, c.name as clinic_name, c.location as clinic_location
                FROM appointments a
                LEFT JOIN users p ON a.patient_id = p._id
                LEFT JOIN clinics c ON a.clinic_id = c._id
                WHERE a.doctor_id = ? 
                AND a.date = ? 
                AND a.status != 'cancelled'
            '''
            params = [doctor_id_int, today]
            
            if clinic_id_str:
                try:
                    clinic_id_int = int(clinic_id_str)
                    query += " AND a.clinic_id = ?"
                    params.append(clinic_id_int)
                except ValueError:
                    return jsonify({"error": "Invalid clinic_id format"}), 400
            
            query += " ORDER BY a.start_time ASC"
            
            cursor.execute(query, params)
            appointments = cursor.fetchall()
            
            # Convert to list of dicts
            appointments_list = []
            for apt in appointments:
                apt_dict = dict(apt)
                apt_dict["_id"] = apt_dict["_id"]
                apt_dict["patient_id"] = str(apt_dict["patient_id"])
                apt_dict["clinic_id"] = str(apt_dict["clinic_id"])
                appointments_list.append(apt_dict)
            
            # ────────────────────────────────────────────────
            # Get exceptions for today
            # ────────────────────────────────────────────────
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            today_exceptions = {}
            
            if result and result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                    
                    for aff in affiliations:
                        clinic_id_val = str(aff.get("clinic_id"))
                        
                        # If specific clinic requested, only return that one
                        if clinic_id_str and clinic_id_str != clinic_id_val:
                            continue
                        
                        for ex in aff.get("exceptions", []):
                            if ex.get("date") == today:
                                today_exceptions[clinic_id_val] = {
                                    "status": ex.get("status"),
                                    "reason": ex.get("reason"),
                                    "new_start_time": ex.get("new_start_time"),
                                    "new_end_time": ex.get("new_end_time")
                                }
                                break
                except:
                    pass
            
            # Format the response
            response = {
                "appointments": appointments_list,
                "date": today,
            }
            
            if clinic_id_str:
                response["today_exception"] = today_exceptions.get(clinic_id_str)
            else:
                response["today_exceptions"] = today_exceptions
            
            return jsonify(response), 200
            
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error getting today's appointments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


@app.route('/api/doctor/<doctor_id>/all-appointments', methods=['GET'])
def get_all_doctor_appointments(doctor_id):
    """
    Get all doctor appointments (not just today)
    - Supports Pagination: ?page=1&limit=20
    - Supports Filtering: ?status=completed&clinic_id=xxx&from_date=2024-01-01&to_date=2024-12-31
    """
    try:
        doctor_id_int = int(doctor_id)
        
        # Read query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        
        status_filter = request.args.get('status')
        clinic_id_filter = request.args.get('clinic_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_clause = "WHERE a.doctor_id = ?"
            params = [doctor_id_int]
            
            if status_filter:
                where_clause += " AND a.status = ?"
                params.append(status_filter)
            
            if clinic_id_filter:
                try:
                    clinic_id_int = int(clinic_id_filter)
                    where_clause += " AND a.clinic_id = ?"
                    params.append(clinic_id_int)
                except ValueError:
                    return jsonify({"error": "Invalid clinic_id format"}), 400
            
            if from_date:
                where_clause += " AND a.date >= ?"
                params.append(from_date)
            
            if to_date:
                where_clause += " AND a.date <= ?"
                params.append(to_date)
            
            # Query for total count
            count_query = f"SELECT COUNT(*) as total FROM appointments a {where_clause}"
            cursor.execute(count_query, params)
            total_result = cursor.fetchone()
            total = total_result["total"] if total_result else 0
            
            # Main query with joins
            query = f'''
                SELECT 
                    a._id, a.patient_id, a.date, a.start_time, a.end_time, 
                    a.type, a.status, a.price, a.created_at,
                    p.name as patient_name, p.image as patient_image,
                    c._id as clinic_id, c.name as clinic_name, c.location as clinic_location
                FROM appointments a
                LEFT JOIN users p ON a.patient_id = p._id
                LEFT JOIN clinics c ON a.clinic_id = c._id
                {where_clause}
                ORDER BY a.date DESC, a.start_time DESC
                LIMIT ? OFFSET ?
            '''
            
            cursor.execute(query, params + [limit, skip])
            appointments = cursor.fetchall()
            
            # Convert to list of dicts
            appointments_list = []
            for apt in appointments:
                apt_dict = dict(apt)
                apt_dict["_id"] = apt_dict["_id"]
                apt_dict["patient_id"] = str(apt_dict["patient_id"])
                apt_dict["clinic_id"] = str(apt_dict["clinic_id"])
                appointments_list.append(apt_dict)
            
            return jsonify({
                "success": True,
                "appointments": appointments_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if limit > 0 else 0
                }
            }), 200
            
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error getting all appointments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/weekly-schedule', methods=['GET'])
def get_weekly_schedule(doctor_id, clinic_id):
    """
    Get weekly schedule for a doctor at a specific clinic
    """
    try:
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404
            
            # Parse affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Find the specific clinic affiliation
            affiliation = None
            for aff in affiliations:
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation = aff
                    break
            
            if not affiliation:
                return jsonify({
                    "weekly_schedule": [],
                    "slot_duration": {
                        "consultation": 30,
                        "follow_up": 20,
                        "buffer_time": 10
                    },
                    "message": "No affiliation found"
                }), 200
            
            weekly_schedule = affiliation.get('weekly_schedule', [])
            slot_duration = affiliation.get('slot_duration', {
                "consultation": 30,
                "follow_up": 20,
                "buffer_time": 10
            })
            
            return jsonify({
                "weekly_schedule": weekly_schedule,
                "slot_duration": slot_duration
            }), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error in get_weekly_schedule: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/weekly-schedule', methods=['POST', 'PUT'])
def update_weekly_schedule(doctor_id, clinic_id):
    """
    Update weekly schedule for a doctor at a specific clinic
    """
    try:
        data = request.get_json()
        weekly_schedule = data.get('weekly_schedule', [])
        
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get current affiliations
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404
            
            # Parse affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Find and update the specific clinic affiliation
            updated = False
            for aff in affiliations:
                if aff.get("clinic_id") == clinic_id_int:
                    aff["weekly_schedule"] = weekly_schedule
                    updated = True
                    break
            
            if not updated:
                return jsonify({"error": "Clinic affiliation not found"}), 404
            
            # Save back to database
            cursor.execute(
                "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                (json.dumps(affiliations), datetime.utcnow().isoformat(), doctor_id_int)
            )
            
            return jsonify({
                "success": True,
                "message": "Weekly schedule updated successfully"
            }), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error in update_weekly_schedule: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def calculate_doctor_rating(doctor_id: int):
    """Helper to recalculate doctor's average rating"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE doctor_id = ?", (doctor_id,))
        stats = cursor.fetchone()
        
        avg_rating = round(stats["avg_rating"] or 0, 1)
        count = stats["count"] or 0
        
        cursor.execute('''
            UPDATE users SET rating = ?, rating_count = ?, updated_at = ?
            WHERE _id = ?
        ''', (avg_rating, count, datetime.now(timezone.utc).isoformat(), doctor_id))
        
        return avg_rating, count
# ────────────────────────────────────────────────
# Reviews Management (SQLite Version)
# ────────────────────────────────────────────────
@app.route('/api/doctor/<int:doctor_id>/reviews', methods=['GET', 'OPTIONS'])
def get_doctor_reviews(doctor_id):
    """جلب جميع التقييمات الخاصة بدكتور معين"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # جلب التقييمات مع اسم المريض وصورته
            query = '''
                SELECT 
                    r._id,
                    r.rating,
                    r.comment,
                    r.created_at,
                    u._id as patient_id,
                    u.name as patient_name,
                    u.image as patient_image,
                    a.type as visit_type
                FROM reviews r
                LEFT JOIN users u ON r.patient_id = u._id
                LEFT JOIN appointments a ON r.appointment_id = a._id
                WHERE r.doctor_id = ?
                ORDER BY r.created_at DESC
            '''
            cursor.execute(query, (doctor_id,))
            rows = cursor.fetchall()
            
            reviews = []
            for row in rows:
                review = dict(row)
                review["_id"] = str(review["_id"])
                if review.get("patient_id"):
                    review["patient_id"] = str(review["patient_id"])
                
                # إضافة صورة افتراضية للمريض إذا لم توجد
                if not review.get("patient_image"):
                    review["patient_image"] = f"https://ui-avatars.com/api/?name={review.get('patient_name', 'Patient')}&background=0D9488&color=fff&size=64"
                
                reviews.append(review)
            
            # جلب متوسط التقييمات للدكتور
            cursor.execute('''
                SELECT 
                    COALESCE(AVG(rating), 0) as avg_rating,
                    COUNT(*) as total_reviews
                FROM reviews 
                WHERE doctor_id = ?
            ''', (doctor_id,))
            stats = cursor.fetchone()
            
            return jsonify({
                "success": True,
                "reviews": reviews,
                "average_rating": round(stats["avg_rating"] or 0, 1),
                "total_reviews": stats["total_reviews"] or 0
            }), 200
            
    except Exception as e:
        print(f"❌ Error fetching doctor reviews: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/appointments/<int:appointment_id>/review', methods=['POST'])
def add_appointment_review(appointment_id):
    """إضافة تقييم جديد لموعد محدد"""
    try:
        data = request.json
        rating = data.get('rating')
        comment = data.get('comment', '')
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')

        if not rating or not patient_id or not doctor_id:
            return jsonify({"error": "Missing required fields"}), 400

        now_iso = datetime.now().isoformat()

        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. إدخال التقييم في جدول reviews
            cursor.execute('''
                INSERT INTO reviews (patient_id, doctor_id, appointment_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (patient_id, doctor_id, appointment_id, rating, comment, now_iso))

            # 2. تحديث حالة الموعد ليكون 'completed' أو تحديث أنه تم تقييمه
            cursor.execute('UPDATE appointments SET status = "completed" WHERE _id = ?', (appointment_id,))

            # 3. تحديث متوسط تقييم الدكتور في جدول users
            cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE doctor_id = ?", (doctor_id,))
            stats = cursor.fetchone()
            
            cursor.execute('''
                UPDATE users 
                SET rating = ?, rating_count = ?
                WHERE _id = ?
            ''', (round(stats["avg_rating"] or 0, 1), stats["count"] or 0, doctor_id))

            conn.commit()
            return jsonify({"success": True, "message": "Review submitted successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "You have already reviewed this appointment"}), 400
    except Exception as e:
        print(f"❌ Error adding review: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<review_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def manage_review(review_id):
    """Update or delete a review"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        review_id_int = int(review_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            if request.method == 'PUT':
                # Update review
                data = request.json
                update_fields = []
                params = []
                
                if "rating" in data:
                    rating = int(data["rating"])
                    if rating < 1 or rating > 5:
                        return jsonify({"error": "Rating must be between 1 and 5"}), 400
                    update_fields.append("rating = ?")
                    params.append(rating)
                
                if "comment" in data:
                    update_fields.append("comment = ?")
                    params.append(data["comment"])
                
                if not update_fields:
                    return jsonify({"error": "No fields to update"}), 400
                
                # Get old review to update doctor's rating
                cursor.execute("SELECT doctor_id, rating FROM reviews WHERE _id = ?", (review_id_int,))
                old_review = cursor.fetchone()
                
                if not old_review:
                    return jsonify({"error": "Review not found"}), 404
                
                update_fields.append("updated_at = ?")
                params.append(now_iso)
                params.append(review_id_int)
                
                cursor.execute(f"UPDATE reviews SET {', '.join(update_fields)} WHERE _id = ?", params)
                
                # If rating was updated, recalculate doctor's average
                if "rating" in [f.split('=')[0].strip() for f in update_fields if '=' in f]:
                    cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE doctor_id = ?", (old_review["doctor_id"],))
                    stats = cursor.fetchone()
                    
                    cursor.execute('''
                        UPDATE users 
                        SET rating = ?, rating_count = ?, updated_at = ?
                        WHERE _id = ?
                    ''', (round(stats["avg_rating"] or 0, 1), stats["count"] or 0, now_iso, old_review["doctor_id"]))
                
                conn.commit()
                return jsonify({"message": "Review updated successfully"}), 200
                
            elif request.method == 'DELETE':
                # Delete review
                cursor.execute("SELECT doctor_id FROM reviews WHERE _id = ?", (review_id_int,))
                review = cursor.fetchone()
                
                if not review:
                    return jsonify({"error": "Review not found"}), 404
                
                doctor_id = review["doctor_id"]
                
                cursor.execute("DELETE FROM reviews WHERE _id = ?", (review_id_int,))
                
                # Recalculate doctor's average
                cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE doctor_id = ?", (doctor_id,))
                stats = cursor.fetchone()
                
                cursor.execute('''
                    UPDATE users 
                    SET rating = ?, rating_count = ?, updated_at = ?
                    WHERE _id = ?
                ''', (round(stats["avg_rating"] or 0, 1), stats["count"] or 0, now_iso, doctor_id))
                
                conn.commit()
                return jsonify({"message": "Review deleted successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid review ID format"}), 400
    except Exception as e:
        print(f"❌ Error managing review: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/appointments/<appointment_id>/can-review', methods=['GET', 'OPTIONS'])
def check_if_can_review(appointment_id):
    """Check if an appointment can be reviewed (completed and not reviewed yet)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        appointment_id_int = int(appointment_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if appointment exists and is completed
            cursor.execute("SELECT status FROM appointments WHERE _id = ?", (appointment_id_int,))
            appointment = cursor.fetchone()
            
            if not appointment or appointment["status"] != "completed":
                return jsonify({"can_review": False, "reason": "Appointment not completed"}), 200
            
            # Check if review already exists
            cursor.execute("SELECT _id, rating, comment FROM reviews WHERE appointment_id = ?", (appointment_id_int,))
            existing_review = cursor.fetchone()
            
            if existing_review:
                return jsonify({
                    "can_review": False,
                    "reason": "Already reviewed",
                    "review": {
                        "rating": existing_review["rating"],
                        "comment": existing_review["comment"] or ""
                    }
                }), 200
            
            return jsonify({"can_review": True}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid appointment ID format"}), 400
    except Exception as e:
        print(f"❌ Error checking review status: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/appointments/<appointment_id>/check-review', methods=['GET', 'OPTIONS'])
def check_appointment_review(appointment_id):
    """Check if an appointment already has a review"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        appointment_id_int = int(appointment_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT _id, rating, comment FROM reviews WHERE appointment_id = ?", (appointment_id_int,))
            review = cursor.fetchone()
            
            if review:
                return jsonify({
                    "has_review": True,
                    "review_id": review["_id"],
                    "rating": review["rating"],
                    "comment": review["comment"] or ""
                }), 200
            
            return jsonify({"has_review": False}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid appointment ID format"}), 400
    except Exception as e:
        print(f"❌ Error checking review: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Doctor Quick Stats (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/quick-stats', methods=['GET'])
def get_doctor_quick_stats(doctor_id):
    try:
        doctor_id_int = int(doctor_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Today's appointments count (excluding cancelled/rejected)
            cursor.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND date = ? AND status NOT IN ('cancelled', 'rejected')
            ''', (doctor_id_int, today))
            today_count = cursor.fetchone()["count"] or 0
            
            # Pending appointments count
            cursor.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND status = 'pending'
            ''', (doctor_id_int,))
            pending_count = cursor.fetchone()["count"] or 0
            
            # Doctor's rating
            cursor.execute("SELECT rating, rating_count, clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            doctor = cursor.fetchone()
            
            avg_rating = doctor["rating"] if doctor else 0
            
            # Number of clinics (parse JSON)
            clinics_count = 0
            if doctor and doctor["clinic_affiliations"]:
                try:
                    affiliations = json.loads(doctor["clinic_affiliations"])
                    clinics_count = len(affiliations)
                except:
                    clinics_count = 0
            
            return jsonify({
                "today_appointments": today_count,
                "pending_appointments": pending_count,
                "average_rating": avg_rating,
                "clinics_count": clinics_count,
            }), 200
            
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error in quick stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Doctor Exceptions (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/exceptions', methods=['GET'])
def get_doctor_exceptions(doctor_id):
    try:
        doctor_id_int = int(doctor_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404
            
            all_exceptions = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                    
                    for aff in affiliations:
                        clinic_id = aff.get("clinic_id")
                        for ex in aff.get("exceptions", []):
                            all_exceptions.append({
                                **ex,
                                "clinic_id": str(clinic_id)
                            })
                except:
                    pass
            
            return jsonify({"exceptions": all_exceptions}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        print(f"Error getting exceptions: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Available Slots (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/available-slots', methods=['GET'])
def get_available_slots(doctor_id):
    try:
        doctor_id_int = int(doctor_id)
        date_str = request.args.get('date')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM slots WHERE doctor_id = ? AND status = 'available'"
            params = [doctor_id_int]
            
            if date_str:
                query += " AND date = ?"
                params.append(date_str)
            
            query += " ORDER BY date ASC, start_time ASC"
            
            cursor.execute(query, params)
            slots = cursor.fetchall()
            
            # Convert to list of dicts
            slots_list = []
            for slot in slots:
                slot_dict = dict(slot)
                slot_dict["_id"] = slot_dict["_id"]
                slots_list.append(slot_dict)
            
            return jsonify({"slots": slots_list}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid doctor ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Add Manual Available Slot (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/manual-slot', methods=['POST'])
def add_manual_available_slot(doctor_id):
    try:
        data = request.get_json()
        required = ["clinic_id", "date", "start_time", "end_time", "type", "price"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(data["clinic_id"])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if doctor is affiliated with this clinic
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404
            
            # Parse affiliations and check clinic
            is_affiliated = False
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                    for aff in affiliations:
                        if aff.get("clinic_id") == clinic_id_int:
                            is_affiliated = True
                            break
                except:
                    pass
            
            if not is_affiliated:
                return jsonify({"error": "Doctor not affiliated with this clinic"}), 403
            
            # Calculate duration
            try:
                start_dt = datetime.strptime(data["start_time"], "%H:%M")
                end_dt = datetime.strptime(data["end_time"], "%H:%M")
                duration = int((end_dt - start_dt).total_seconds() / 60)
                if duration <= 0:
                    return jsonify({"error": "End time must be after start time"}), 400
            except:
                return jsonify({"error": "Invalid time format"}), 400
            
            # Check for overlapping slots
            cursor.execute('''
                SELECT _id FROM slots 
                WHERE doctor_id = ? AND date = ? 
                AND (
                    (start_time < ? AND end_time > ?) OR
                    (start_time >= ? AND end_time <= ?)
                )
            ''', (doctor_id_int, data["date"], data["end_time"], data["start_time"], data["start_time"], data["end_time"]))
            
            if cursor.fetchone():
                return jsonify({"error": "This time slot overlaps with an existing one"}), 409
            
            now_iso = datetime.utcnow().isoformat()
            
            # Insert the manual slot
            cursor.execute('''
                INSERT INTO slots 
                (doctor_id, clinic_id, date, start_time, end_time, duration_minutes, 
                 type, price, status, is_manual, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doctor_id_int, clinic_id_int, data["date"], data["start_time"], data["end_time"],
                duration, data["type"], float(data["price"]), "available", 1, now_iso, now_iso
            ))
            
            slot_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Manual slot added successfully",
                "slot_id": slot_id
            }), 201
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Update Available Slot (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/available-slots/<slot_id>', methods=['PUT'])
def update_available_slot(doctor_id, slot_id):
    try:
        data = request.get_json()
        doctor_id_int = int(doctor_id)
        slot_id_int = int(slot_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if slot exists and is available
            cursor.execute('''
                SELECT _id FROM slots 
                WHERE _id = ? AND doctor_id = ? AND status = 'available'
            ''', (slot_id_int, doctor_id_int))
            
            if not cursor.fetchone():
                return jsonify({"error": "Available slot not found or already booked"}), 404
            
            update_fields = []
            params = []
            
            if "start_time" in data:
                update_fields.append("start_time = ?")
                params.append(data["start_time"])
            if "end_time" in data:
                update_fields.append("end_time = ?")
                params.append(data["end_time"])
            if "type" in data:
                update_fields.append("type = ?")
                params.append(data["type"])
            if "price" in data:
                update_fields.append("price = ?")
                params.append(float(data["price"]))
            
            # If times changed, recalculate duration
            if "start_time" in data or "end_time" in data:
                # Get current or new times
                cursor.execute("SELECT start_time, end_time FROM slots WHERE _id = ?", (slot_id_int,))
                current = cursor.fetchone()
                
                start = data.get("start_time", current["start_time"])
                end = data.get("end_time", current["end_time"])
                
                try:
                    start_dt = datetime.strptime(start, "%H:%M")
                    end_dt = datetime.strptime(end, "%H:%M")
                    duration = int((end_dt - start_dt).total_seconds() / 60)
                    if duration <= 0:
                        return jsonify({"error": "Invalid time range"}), 400
                    update_fields.append("duration_minutes = ?")
                    params.append(duration)
                except:
                    return jsonify({"error": "Invalid time format"}), 400
            
            if not update_fields:
                return jsonify({"message": "No changes made"}), 200
            
            update_fields.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(slot_id_int)
            
            cursor.execute(f"UPDATE slots SET {', '.join(update_fields)} WHERE _id = ?", params)
            conn.commit()
            
            return jsonify({"success": True, "message": "Slot updated successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Delete Available Slot (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/available-slots/<slot_id>', methods=['DELETE'])
def delete_available_slot(doctor_id, slot_id):
    try:
        doctor_id_int = int(doctor_id)
        slot_id_int = int(slot_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Delete only if available and belongs to doctor
            cursor.execute('''
                DELETE FROM slots 
                WHERE _id = ? AND doctor_id = ? AND status = 'available'
            ''', (slot_id_int, doctor_id_int))
            
            if cursor.rowcount == 0:
                return jsonify({
                    "error": "Slot not found or already booked or belongs to another doctor"
                }), 404
            
            conn.commit()
            
            return jsonify({"success": True, "message": "Slot deleted successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ────────────────────────────────────────────────
# Update Available Slot (SQLite Version)
# ────────────────────────────────────────────────

from datetime import datetime

@app.route('/api/doctor/<doctor_id>/available-slots/<slot_id>', methods=['PUT'])
def update_doctor_slot_v2(doctor_id, slot_id): # تم تغيير اسم الدالة هنا لتجنب التكرار
    try:
        data = request.get_json()
        doctor_id_int = int(doctor_id)
        slot_id_int = int(slot_id)
        
        with get_db() as conn:
            # استخدام row_factory للوصول للبيانات بأسماء الأعمدة بدلاً من الأرقام
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            
            # التأكد من وجود الموعد وأنه متاح للطبيب المحدد
            cursor.execute('''
                SELECT * FROM slots 
                WHERE _id = ? AND doctor_id = ? AND status = 'available'
            ''', (slot_id_int, doctor_id_int))
            
            slot = cursor.fetchone()
            if not slot:
                return jsonify({"error": "Available slot not found or already booked"}), 404
            
            update_fields = []
            params = []
            
            # حقول التحديث الديناميكي
            for field in ["type", "price", "start_time", "end_time"]:
                if field in data:
                    val = data[field]
                    if field == "price": val = float(val)
                    update_fields.append(f"{field} = ?")
                    params.append(val)
            
            # إعادة حساب المدة إذا تغير الوقت
            if "start_time" in data or "end_time" in data:
                start = data.get("start_time", slot["start_time"])
                end = data.get("end_time", slot["end_time"])
                
                try:
                    start_dt = datetime.strptime(start, "%H:%M")
                    end_dt = datetime.strptime(end, "%H:%M")
                    duration = int((end_dt - start_dt).total_seconds() / 60)
                    
                    if duration <= 0:
                        return jsonify({"error": "End time must be after start time"}), 400
                        
                    update_fields.append("duration_minutes = ?")
                    params.append(duration)
                except ValueError:
                    return jsonify({"error": "Invalid time format. Use HH:MM"}), 400
            
            if not update_fields:
                return jsonify({"message": "No changes made"}), 200
            
            # إضافة وقت التحديث والمعرف
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(slot_id_int)
            
            query = f"UPDATE slots SET {', '.join(update_fields)} WHERE _id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            return jsonify({"success": True, "message": "Slot updated successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID or price format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ────────────────────────────────────────────────
# Delete Available Slot (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/available-slots/<slot_id>', methods=['DELETE'])
def delete_doctor_slot_v2(doctor_id, slot_id): # تم تغيير الاسم هنا ليكون فريداً
    try:
        doctor_id_int = int(doctor_id)
        slot_id_int = int(slot_id)
        
        with get_db() as conn:
            # استخدام sqlite3.Row يسهل قراءة البيانات بأسماء الأعمدة
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. التحقق من وجود الموعد قبل الحذف (اختياري للـ Debugging كما فعلت أنت)
            cursor.execute("SELECT date, start_time, status, doctor_id FROM slots WHERE _id = ?", (slot_id_int,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"Slot exists: date={existing['date']}, start_time={existing['start_time']}, status={existing['status']}, doctor_id={existing['doctor_id']}")
            else:
                print("Slot not found in database")
            
            # 2. تنفيذ عملية الحذف بشرط: المعرف، هوية الطبيب، وحالة الموعد (متاح)
            cursor.execute('''
                DELETE FROM slots 
                WHERE _id = ? AND doctor_id = ? AND status = 'available'
            ''', (slot_id_int, doctor_id_int))
            
            print(f"Deletion result → deleted_count = {cursor.rowcount}")
            
            if cursor.rowcount == 0:
                # إذا لم يتم حذف أي سطر، فهذا يعني أن الموعد إما غير موجود، أو محجوز، أو لا يخص هذا الطبيب
                return jsonify({
                    "error": "Slot not found, already booked, or belongs to another doctor",
                    "debug": {
                        "slot_id": slot_id_int,
                        "doctor_id": doctor_id_int
                    }
                }), 404
            
            conn.commit()
            return jsonify({"success": True, "message": "Slot deleted successfully"}), 200
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ────────────────────────────────────────────────
# Generate Slots in Range (SQLite Version)
# ────────────────────────────────────────────────

from datetime import datetime, timedelta

@app.route('/api/doctor/<doctor_id>/generate-slots-range', methods=['POST'])
def generate_slots_in_range(doctor_id):
    try:
        data = request.get_json()
        required = ["clinic_id", "date", "start_time", "end_time"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        doctor_id_int = int(doctor_id)
        clinic_id_int = int(data["clinic_id"])
        date_str = data["date"]
        
        print(f"🔍 Generating slots for doctor: {doctor_id}, clinic: {clinic_id_int}")

        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Get doctor data
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                print("❌ Doctor not found")
                return jsonify({"error": "Doctor not found"}), 404

            # 2. Find affiliation
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            affiliation = None
            for aff in affiliations:
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation = aff
                    break

            if not affiliation:
                print(f"❌ No affiliation found for clinic {clinic_id_int}")
                return jsonify({
                    "error": "Doctor not affiliated with this clinic",
                    "debug": {
                        "doctor_id": doctor_id,
                        "clinic_id": clinic_id_int,
                        "available_affiliations": [a.get('clinic_id') for a in affiliations]
                    }
                }), 403

            print("✅ Affiliation found, proceeding with slot generation")

            # Get settings
            durations = affiliation.get("slot_duration", {})
            consultation_min = durations.get("consultation", 30)
            follow_up_min = durations.get("follow_up", 20)
            buffer_min = durations.get("buffer_time", 10)
            prices = affiliation.get("prices", {"consultation": 0, "follow_up": 0})

            # 3. Parse times
            try:
                start_dt = datetime.strptime(f"{date_str} {data['start_time']}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {data['end_time']}", "%Y-%m-%d %H:%M")
            except Exception as e:
                print(f"❌ Date parsing error: {e}")
                return jsonify({"error": "Invalid date or time format"}), 400

            if start_dt >= end_dt:
                return jsonify({"error": "End time must be after start time"}), 400

            # 4. Generate slots
            slot_types = [
                ("consultation", consultation_min, prices.get("consultation", 0)),
                ("follow_up", follow_up_min, prices.get("follow_up", 0))
            ]
            
            created_slots = []
            current_time = start_dt
            now_iso = datetime.utcnow().isoformat()

            while current_time + timedelta(minutes=min(consultation_min, follow_up_min)) <= end_dt:
                for slot_type, duration, price in slot_types:
                    slot_end = current_time + timedelta(minutes=duration)
                    
                    if slot_end > end_dt:
                        continue

                    # Check for overlapping slots
                    cursor.execute('''
                        SELECT _id FROM slots 
                        WHERE doctor_id = ? AND date = ? 
                        AND (
                            (start_time < ? AND end_time > ?) OR
                            (start_time >= ? AND end_time <= ?)
                        )
                    ''', (doctor_id_int, date_str, slot_end.strftime("%H:%M"), current_time.strftime("%H:%M"), 
                          current_time.strftime("%H:%M"), slot_end.strftime("%H:%M")))
                    
                    overlapping = cursor.fetchone()

                    if not overlapping:
                        # Insert new slot
                        cursor.execute('''
                            INSERT INTO slots 
                            (doctor_id, clinic_id, date, start_time, end_time, duration_minutes, 
                             type, price, status, created_at, updated_at, is_manual)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            doctor_id_int, clinic_id_int, date_str,
                            current_time.strftime("%H:%M"), slot_end.strftime("%H:%M"),
                            duration, slot_type, float(price), "available",
                            now_iso, now_iso, 0
                        ))
                        
                        created_slots.append(cursor.lastrowid)
                        print(f"✅ Created slot: {current_time.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}")

                    # Move to next time slot
                    current_time = slot_end + timedelta(minutes=buffer_min)
                    break  # Exit for loop to start with first type at new time

                else:
                    # If for loop completed without break, add buffer
                    current_time += timedelta(minutes=buffer_min)

            conn.commit()

            return jsonify({
                "success": True,
                "message": f"Successfully created {len(created_slots)} slots",
                "count": len(created_slots)
            }), 201

    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"❌ Error in generate_slots_in_range: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Affiliate Doctor to Clinic (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/affiliate', methods=['POST'])
def affiliate_doctor_to_clinic(doctor_id, clinic_id):
    """
    Affiliate doctor with a new clinic with settings
    """
    try:
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if doctor exists
            cursor.execute("SELECT name, clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            doctor = cursor.fetchone()
            if not doctor:
                return jsonify({"error": "Doctor not found"}), 404
                
            # Check if clinic exists
            cursor.execute("SELECT name FROM clinics WHERE _id = ?", (clinic_id_int,))
            clinic = cursor.fetchone()
            if not clinic:
                return jsonify({"error": "Clinic not found"}), 404
                
            # Parse existing affiliations
            affiliations = []
            if doctor["clinic_affiliations"]:
                try:
                    affiliations = json.loads(doctor["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Check if already affiliated
            for aff in affiliations:
                if aff.get("clinic_id") == clinic_id_int:
                    return jsonify({"error": "Doctor already affiliated with this clinic"}), 400
            
            # Get settings from request or use defaults
            data = request.get_json() or {}
            
            # Create new affiliation
            now_iso = datetime.utcnow().isoformat()
            new_affiliation = {
                "clinic_id": clinic_id_int,
                "is_active": True,
                "joined_at": now_iso,
                "slot_duration": {
                    "consultation": int(data.get("consultation_duration", 30)),
                    "follow_up": int(data.get("follow_up_duration", 20)),
                    "buffer_time": int(data.get("buffer_time", 10))
                },
                "prices": {
                    "consultation": float(data.get("consultation_price", 0)),
                    "follow_up": float(data.get("follow_up_price", 0))
                },
                "weekly_schedule": data.get("weekly_schedule", []),
                "exceptions": data.get("exceptions", [])
            }
            
            # Add affiliation
            affiliations.append(new_affiliation)
            
            # Save back to database
            cursor.execute(
                "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                (json.dumps(affiliations), now_iso, doctor_id_int)
            )
            
            return jsonify({
                "success": True,
                "message": f"Doctor {doctor['name']} affiliated with clinic {clinic['name']} successfully",
                "affiliation": new_affiliation
            }), 201
            
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"❌ Error affiliating doctor with clinic: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================================================
# Weekly Schedule Management - CRUD Operations (SQLite Version)
# ================================================

@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/weekly-schedule', methods=['POST'])
def add_weekly_schedule_slot(doctor_id, clinic_id):
    """
    Add new slot to weekly schedule
    """
    try:
        data = request.get_json()
        required = ["day", "start_time", "end_time"]
        if not all(k in data for k in required):
            return jsonify({"error": "Incomplete data"}), 400

        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get doctor's affiliations
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404

            # Parse affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Find the affiliation
            affiliation_index = None
            for i, aff in enumerate(affiliations):
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation_index = i
                    break

            if affiliation_index is None:
                return jsonify({"error": "Doctor not affiliated with this clinic"}), 403

            # Create new slot
            import uuid
            new_slot = {
                "_id": str(uuid.uuid4()),  # Generate unique ID for the slot
                "day": data["day"],
                "start_time": data["start_time"],
                "end_time": data["end_time"],
                "created_at": datetime.utcnow().isoformat()
            }

            # Add slot to weekly schedule
            if "weekly_schedule" not in affiliations[affiliation_index]:
                affiliations[affiliation_index]["weekly_schedule"] = []
            
            affiliations[affiliation_index]["weekly_schedule"].append(new_slot)
            
            # Save back to database
            cursor.execute(
                "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                (json.dumps(affiliations), datetime.utcnow().isoformat(), doctor_id_int)
            )

            return jsonify({
                "success": True,
                "message": "Slot added successfully",
                "slot": new_slot
            }), 201

    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error in add_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/weekly-schedule/<slot_id>', methods=['PUT'])
def update_weekly_schedule_slot(doctor_id, clinic_id, slot_id):
    """
    Update slot in weekly schedule
    """
    try:
        data = request.get_json()
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get doctor's affiliations
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404

            # Parse affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Find the affiliation
            affiliation_index = None
            for i, aff in enumerate(affiliations):
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation_index = i
                    break

            if affiliation_index is None:
                return jsonify({"error": "Doctor not affiliated with this clinic"}), 403

            # Find and update the slot
            slot_found = False
            for slot in affiliations[affiliation_index].get("weekly_schedule", []):
                if slot.get("_id") == slot_id:
                    slot["day"] = data["day"]
                    slot["start_time"] = data["start_time"]
                    slot["end_time"] = data["end_time"]
                    slot["updated_at"] = datetime.utcnow().isoformat()
                    slot_found = True
                    break

            if not slot_found:
                return jsonify({"error": "Slot not found"}), 404
            
            # Save back to database
            cursor.execute(
                "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                (json.dumps(affiliations), datetime.utcnow().isoformat(), doctor_id_int)
            )

            return jsonify({
                "success": True,
                "message": "Slot updated successfully"
            }), 200

    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error in update_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/<doctor_id>/clinics/<clinic_id>/weekly-schedule/<slot_id>', methods=['DELETE'])
def delete_weekly_schedule_slot(doctor_id, clinic_id, slot_id):
    """
    Delete slot from weekly schedule
    """
    try:
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get doctor's affiliations
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"error": "Doctor not found"}), 404

            # Parse affiliations
            affiliations = []
            if result["clinic_affiliations"]:
                try:
                    affiliations = json.loads(result["clinic_affiliations"])
                except:
                    affiliations = []
            
            # Find the affiliation
            affiliation_index = None
            for i, aff in enumerate(affiliations):
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation_index = i
                    break

            if affiliation_index is None:
                return jsonify({"error": "Doctor not affiliated with this clinic"}), 403

            # Remove the slot
            original_length = len(affiliations[affiliation_index].get("weekly_schedule", []))
            affiliations[affiliation_index]["weekly_schedule"] = [
                slot for slot in affiliations[affiliation_index].get("weekly_schedule", [])
                if slot.get("_id") != slot_id
            ]
            
            if len(affiliations[affiliation_index]["weekly_schedule"]) == original_length:
                return jsonify({"error": "Slot not found"}), 404
            
            # Save back to database
            cursor.execute(
                "UPDATE users SET clinic_affiliations = ?, updated_at = ? WHERE _id = ?",
                (json.dumps(affiliations), datetime.utcnow().isoformat(), doctor_id_int)
            )

            return jsonify({
                "success": True,
                "message": "Slot deleted successfully"
            }), 200

    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400
    except Exception as e:
        print(f"Error in delete_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Update Appointment Status (SQLite Version)
# ────────────────────────────────────────────────

@app.route('/api/appointments/<appointment_id>/status', methods=['PATCH'])
def update_appointment_status(appointment_id):
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "status field is required"}), 400

        new_status = data['status']
        valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed', 'delayed']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Allowed: {valid_statuses}"}), 400

        appointment_id_int = int(appointment_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE appointments 
                SET status = ?, updated_at = ?
                WHERE _id = ?
            ''', (new_status, datetime.utcnow().isoformat(), appointment_id_int))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Appointment not found"}), 404

            conn.commit()
            
            return jsonify({"success": True, "message": f"Status updated to {new_status}"}), 200

    except ValueError:
        return jsonify({"error": "Invalid appointment ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
# Manager Global Analytics (Total Appointments + Revenue)
# ────────────────────────────────────────────────
@app.route('/api/manager/analytics', methods=['GET'])
def get_manager_analytics():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # إجمالي المواعيد
            cursor.execute("SELECT COUNT(*) as total FROM appointments")
            total_appointments = cursor.fetchone()["total"] or 0
            
            # إجمالي الإيرادات (فقط المواعيد المكتملة أو المؤكدة)
            cursor.execute('''
                SELECT COALESCE(SUM(price), 0) as total_revenue 
                FROM appointments 
                WHERE status IN ('completed', 'confirmed')
            ''')
            total_revenue = float(cursor.fetchone()["total_revenue"] or 0)
            
            # إحصائيات إضافية (اختياري)
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                FROM appointments
            ''')
            status_stats = cursor.fetchone()
            
            return jsonify({
                "success": True,
                "total_appointments": total_appointments,
                "total_revenue": total_revenue,
                "pending_appointments": status_stats["pending"] or 0,
                "confirmed_appointments": status_stats["confirmed"] or 0,
                "completed_appointments": status_stats["completed"] or 0
            }), 200
            
    except Exception as e:
        print(f"Error in manager analytics: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ────────────────────────────────────────────────
# Chat Bot Routes (No changes needed - these are external API calls)
# ────────────────────────────────────────────────

# The chat bot routes (/health, /chat, /chat/specialty-only) remain the same
# as they don't directly interact with the database.
# They use the rag_openai module and OpenRouter API.
    
##
# chat_bot
# backend/app.py
# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback
import requests
import time


# استيراد كل الدوال من rag_openai (المصدر الوحيد)
# استبدل الاستيراد القديم بهذا:
from rag_openai import (
    generate_medical_response,
    detect_language,
    is_greeting_or_non_medical,
    get_greeting_response,
    smart_medical_query,
    get_specialty_arabic,
    get_urgency_arabic,
    get_urgency_english,
    call_openrouter,
    check_intent_with_llm,
    get_response_prompt,
    generate_vip_personalized_response,
    generate_dynamic_response_with_llm,
    get_patient_history   # ← أضف هذه
)

# ========== OPENROUTER CONFIGURATION ==========
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
import requests # تأكد إنك عامل import للمكتبة دي

# ========== DYNAMIC GREETING GENERATOR ==========
def generate_dynamic_greeting(user_input: str, language: str) -> str:
    """Generate varied greeting responses"""
    
    if language == 'arabic':
        system_prompt = """أنت مساعد طبي ودود. رد على تحية المستخدم بأسلوب ترحيبي مختلف كل مرة.
اطلب منه وصف أعراضه الطبية. استخدم إيموجيز طبية. اجعل الرد قصير (جملتين إلى ثلاث)."""
    else:
        system_prompt = """You are a friendly medical assistant. Respond to greetings with varied, warm welcomes.
Ask the user to describe their symptoms. Use medical emojis. Keep response short (2-3 sentences)."""
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "openrouter/google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.8,
            "max_tokens": 100
        }
        
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        
        # Fallback
        return "🏥 Welcome! How can I help you today? Please describe your symptoms." if language == 'english' else "🏥 أهلاً بك! كيف يمكنني مساعدتك اليوم؟ من فضلك صف أعراضك."
        
    except Exception as e:
        print(f"Greeting generation error: {e}")
        return "🏥 Welcome! 👋 Please describe your medical symptoms." if language == 'english' else "🏥 أهلاً وسهلاً! 🩺 تفضل بوصف الأعراض."


# ========== HELPER FUNCTIONS (اللي مش موجودة في rag_openai) ==========
def build_conversation_context(history, current_message, max_messages=6):
    """Build conversation context from history for medical analysis"""
    if not history:
        return current_message
    
    recent_history = history[-max_messages:]
    context_parts = []
    
    for msg in recent_history:
        if msg.get('suggestedDoctors'):
            continue
        role = "Patient" if not msg.get('isBot', False) else "Assistant"
        text = msg.get('text', '')
        if len(text) > 500:
            text = text[:500] + "..."
        context_parts.append(f"{role}: {text}")
    
    context_parts.append(f"Patient (current): {current_message}")
    context = "\n".join(context_parts)
    
    return f"""Previous conversation:
{context}

Based on the conversation above, analyze the patient's current symptoms and provide appropriate medical guidance."""


def get_response_prompt_with_context(language, context, disease, severity, specialty, urgency, emergency_warning, user_input, full_context):
    """Build prompt with conversation context - uses get_response_prompt from rag_openai"""
    # استخدم الدالة من rag_openai مع السياق الإضافي
    base_prompt = get_response_prompt(
        language, context, disease, severity, 
        specialty, urgency, emergency_warning, user_input
    )
    
    # أضف السياق إذا موجود
    if full_context:
        if language == 'arabic':
            context_section = f"\n\n**سياق المحادثة السابقة:**\n{full_context}\n"
        else:
            context_section = f"\n\n**Conversation Context:**\n{full_context}\n"
        
        # أدخل السياق في بداية الـ prompt
        lines = base_prompt.split('\n')
        if language == 'arabic':
            insert_pos = 2  # بعد السطر الأول
        else:
            insert_pos = 2
        lines.insert(insert_pos, context_section)
        return '\n'.join(lines)
    
    return base_prompt


def generate_medical_response_with_context(full_context, original_message, history):
    """Generate medical response with conversation context"""
    
    user_language = detect_language(original_message)
    print(f"\n🌐 Detected language: {'العربية' if user_language == 'arabic' else 'English'}")
    
    if is_greeting_or_non_medical(original_message, user_language):
        print("👋 Greeting detected - returning friendly response")
        return {
            'success': True,
            'ai_response': get_greeting_response(user_language),
            'language': user_language,
            'is_greeting': True,
            'analysis': {
                'disease': 'N/A',
                'severity': 0,
                'specialty': None,
                'urgency': 'N/A',
                'is_emergency': False
            }
        }
    
    print("🔍 Analyzing symptoms with conversation context...")
    analysis = smart_medical_query(original_message, user_language)
    
    if analysis.get('most_critical'):
        best_match = analysis['most_critical']
        context = best_match.get('text', '')
        disease = best_match.get('disease', 'Unknown')
        severity = best_match.get('severity', 0)
        specialty = best_match.get('specialty', 'General Medicine')
        
        if user_language == 'arabic':
            urgency = get_urgency_arabic(severity)
            specialty_display = get_specialty_arabic(specialty)
        else:
            urgency = get_urgency_english(severity)
            specialty_display = specialty
        
        emergency_warning = analysis.get('emergency_alert') is not None
    else:
        context = "No matching disease found"
        disease = "Not specified" if user_language == 'english' else "غير محدد"
        severity = 0
        specialty = None
        specialty_display = "General Medicine" if user_language == 'english' else "طب عام"
        urgency = get_urgency_arabic(0) if user_language == 'arabic' else get_urgency_english(0)
        emergency_warning = False
    
    # استخدم الدالة المعدلة مع السياق
    prompt = get_response_prompt_with_context(
        user_language, context, disease, severity, 
        specialty_display, urgency, emergency_warning, 
        original_message, full_context
    )
    
    print("🤖 Generating response with AI...")
    ai_response = call_openrouter(prompt, user_language)
    
    # تنظيف الرد
    if ai_response and len(ai_response) > 2:
        if ai_response[0] == '"' and ai_response[-1] == '"':
            ai_response = ai_response[1:-1]
    
    return {
        'success': True,
        'ai_response': ai_response,
        'language': user_language,
        'is_greeting': False,
        'analysis': {
            'disease': disease,
            'severity': severity,
            'specialty': specialty_display if specialty else None,
            'urgency': urgency,
            'is_emergency': emergency_warning
        }
    }


# ========== API ENDPOINTS ==========
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Medical Assistant API"})


@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data['message'].strip()
        history = data.get('history', [])

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        print(f"\n📨 Received: '{user_message}' | History: {len(history)}")

        # بناء السياق
        conversation_context = build_conversation_context(history, user_message)

        # استدعاء الدالة المحدثة
        result = generate_dynamic_response_with_llm(conversation_context, user_message, history)

        print(f"✅ Dynamic LLM decided: type = {result.get('type', 'unknown')} | Message: '{user_message[:60]}...'")

        # SAFE HANDLING
        if isinstance(result, str):
            ai_response = result
            response_type = "general"
            analysis = {}
        else:
            ai_response = result.get('ai_response') or result.get('response') or result.get('content', '')
            response_type = result.get('type', 'general')
            analysis = result.get('analysis') or {}

        if not ai_response or len(str(ai_response).strip()) < 3:
            ai_response = "شكراً لرسالتك. هل يمكنك وصف الأعراض بمزيد من التفصيل؟"

        response_data = {
            "success": True,
            "response": ai_response,
            "reply": ai_response,
            "message": ai_response,
            "type": response_type,
            "language": result.get('language', detect_language(user_message)) if isinstance(result, dict) else detect_language(user_message)
        }

        # ====================== التحديث الجديد ======================
        if response_type == "doctor_request":
            # استخراج التخصص الموصى به من عدة مصادر
            specialty = None
            
            # 1. من analysis
            if isinstance(analysis, dict):
                specialty = analysis.get('specialty')
            
            # 2. من recommended_specialty المباشر
            if not specialty and isinstance(result, dict):
                specialty = result.get('recommended_specialty')
            
            # 3. من specialty_detected
            if not specialty and isinstance(result, dict):
                specialty = result.get('specialty_detected')
            
            # 4. استخراج من الرسالة مباشرة (fallback)
            if not specialty:
                # استخراج التخصص من الرسالة باستخدام extract_specialty_from_message
                specialty = extract_specialty_from_message(user_message)
            
            # 5. آخر fallback
            if not specialty:
                specialty = "Internal Medicine"
            
            # تطبيع التخصص ليتوافق مع قاعدة البيانات
            normalized_specialty = map_to_app_specialty(specialty)
            
            print(f"🎯 Extracted specialty: '{specialty}' → Normalized: '{normalized_specialty}'")

            response_data.update({
                "type": "doctor_request",
                "recommended_specialty": normalized_specialty,
                "original_specialty": specialty,  # للتصحيح
                "show_doctors": True,
                "ai_response": ai_response,
                "response": ai_response,
                "reply": ai_response,
                "message": f"{ai_response}\n\nهل تريد رؤية الدكاترة المتاحين في تخصص **{normalized_specialty}**؟"
            })

        # الحالة العادية للـ medical
        elif response_type == "medical" and isinstance(analysis, dict):
            specialty = analysis.get('specialty')
            
            # تطبيع التخصص للـ medical
            if specialty:
                normalized_specialty = map_to_app_specialty(specialty)
            else:
                normalized_specialty = None
            
            response_data.update({
                "analysis": {
                    "disease": analysis.get('disease', 'Unknown'),
                    "severity": analysis.get('severity', 0),
                    "specialty": normalized_specialty,
                    "original_specialty": specialty,  # للتصحيح
                    "urgency": analysis.get('urgency', ''),
                    "is_emergency": analysis.get('is_emergency', False)
                },
                "specialty_detected": normalized_specialty
            })

        # greeting أو general عادي (بدون تحليل إضافي)
        else:
            pass

        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Error in /chat: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "response": "عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.",
            "reply": "عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.",
            "type": "error"
        }), 200
    

def extract_specialty_from_message(message):
    """استخراج التخصص من الرسالة النصية"""
    if not message:
        return None
    
    message_lower = message.lower()
    
    # خريطة التخصصات والكلمات المفتاحية
    specialty_patterns = {
        "Cardiology": ["قلب", "cardiology", "أمراض القلب", "القلب", "cardiologist"],
        "Pediatrics": ["أطفال", "pediatrics", "اطفال", "pediatric"],
        "Dermatology": ["جلدية", "dermatology", "جلد", "dermatologist"],
        "Neurology": ["أعصاب", "neurology", "مخ", "neurologist"],
        "ENT": ["انف", "أذن", "حنجرة", "ent", "أنف وأذن"],
        "Ophthalmology": ["عيون", "ophthalmology", "عين", "ophthalmologist"],
        "Orthopedics": ["عظام", "orthopedics", "orthopedic"],
        "Psychiatry": ["نفسي", "psychiatry", "psychiatrist"],
        "Internal Medicine": ["باطنة", "internal medicine", "طب باطني"],
    }
    
    for specialty, keywords in specialty_patterns.items():
        for keyword in keywords:
            if keyword in message_lower:
                print(f"🔍 Extracted '{specialty}' from message using keyword '{keyword}'")
                return specialty
    
    return None


@app.route('/chat/specialty-only', methods=['POST'])
def specialty_only():
    """Lightweight endpoint that returns ONLY the detected specialty"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({"specialty": None, "error": "No message"}), 400
        
        intent = check_intent_with_llm(user_input)
        if intent == "greeting":
            return jsonify({"specialty": None, "type": "greeting"})
        
        result = generate_medical_response(user_input)
        
        if result['success']:
            return jsonify({
                "specialty": result['analysis'].get('specialty'),
                "disease": result['analysis'].get('disease'),
                "severity": result['analysis'].get('severity'),
                "is_emergency": result['analysis'].get('is_emergency', False),
                "type": "medical"
            })
        else:
            return jsonify({"specialty": None, "error": result.get('error')}), 500
            
    except Exception as e:
        return jsonify({"specialty": None, "error": str(e)}), 500

# backend/app.py - أضف هذه الدالة بعد الاستيرادات

def map_to_app_specialty(ai_detected):
    """Convert AI detected specialty to match app's dropdown options"""
    if not ai_detected:
        return "Internal Medicine"
    
    val = ai_detected.lower().strip()
    
    # قاموس التحويل - يربط كلام الـ AI بالقيم الموجودة في الـ Dropdown
    mapping = {
        # Pediatrics (أطفال)
        "pediatric": "Pediatrics",
        "pediatrics": "Pediatrics",
        "أطفال": "Pediatrics",
        "اطفال": "Pediatrics",
        "child": "Pediatrics",
        "baby": "Pediatrics",
        "kid": "Pediatrics",
        
        # Internal Medicine (باطنة)
        "internal medicine": "Internal Medicine",
        "internal": "Internal Medicine",
        "باطنة": "Internal Medicine",
        "طب باطني": "Internal Medicine",
        
        # Cardiology (قلب)
        "cardiology": "Cardiology",
        "قلب": "Cardiology",
        "heart": "Cardiology",
        "chest pain": "Cardiology",
        
        # Dermatology (جلدية)
        "dermatology": "Dermatology",
        "جلدية": "Dermatology",
        "skin": "Dermatology",
        "rash": "Dermatology",
        
        # Orthopedics (عظام)
        "orthopedics": "Orthopedics",
        "orthopedic": "Orthopedics",
        "عظام": "Orthopedics",
        "bone": "Orthopedics",
        "joint": "Orthopedics",
        
        # ENT (أنف وأذن وحنجرة)
        "ent": "ENT",
        "ear nose throat": "ENT",
        "أنف وأذن": "ENT",
        "ear": "ENT",
        "throat": "ENT",
        
        # Neurology (مخ وأعصاب)
        "neurology": "Neurology",
        "مخ وأعصاب": "Neurology",
        "brain": "Neurology",
        "nerve": "Neurology",
        "headache": "Neurology",
        "migraine": "Neurology",
        
        # Ophthalmology (عيون)
        "ophthalmology": "Ophthalmology",
        "eye": "Ophthalmology",
        "عيون": "Ophthalmology",
        "vision": "Ophthalmology",
        
        # Urology (مسالك بولية)
        "urology": "Urology",
        "مسالك بولية": "Urology",
        "urinary": "Urology",
        
        # Gastroenterology (جهاز هضمي)
        "gastroenterology": "Gastroenterology",
        "جهاز هضمي": "Gastroenterology",
        "stomach": "Gastroenterology",
        "digest": "Gastroenterology",
        
        # Respiratory Medicine (صدرية)
        "respiratory": "Respiratory Medicine",
        "chest": "Respiratory Medicine",
        "lung": "Respiratory Medicine",
        "صدرية": "Respiratory Medicine",
        "cough": "Respiratory Medicine",
        
        # Psychiatry (نفسية)
        "psychiatry": "Psychiatry",
        "نفسية": "Psychiatry",
        "mental": "Psychiatry",
        "anxiety": "Psychiatry",
        "depression": "Psychiatry",
        
        # Infectious Disease (أمراض معدية)
        "infectious": "Infectious Disease",
        "infection": "Infectious Disease",
        "أمراض معدية": "Infectious Disease",
        "bacteria": "Infectious Disease",
        "virus": "Infectious Disease",
        
        # General Medicine (طب عام)
        "general medicine": "General Medicine",
        "general": "General Medicine",
        "طب عام": "General Medicine",
        "family medicine": "General Medicine",
    }
    
    # البحث عن المفتاح المناسب
    for key, target in mapping.items():
        if key in val:
            print(f"🔄 Mapping: '{ai_detected}' → '{target}'")
            return target
    
    # Fallback إلى Internal Medicine إذا لم يتم العثور على تطابق
    print(f"⚠️ No mapping found for '{ai_detected}', defaulting to Internal Medicine")
    return "Internal Medicine"




# viiiiiiiip

def get_automated_medical_context(patient_id):
    try:
        # الربط مع الداتابيز بتاعتك
        conn = sqlite3.connect('medibook.db') 
        cursor = conn.cursor()
        
        # بنجيب آخر تخصص المريض حجز فيه من جدول الـ appointments
        # تأكد أن اسم الجدول 'appointments' واسم العمود 'specialty' و 'patient_id'
        cursor.execute('''
            SELECT specialty 
            FROM appointments 
            WHERE patient_id = ? 
            ORDER BY appointment_date DESC LIMIT 1
        ''', (patient_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0] # سيرجع مثلاً 'Cardiologist' أو 'Pediatrician'
        return "General"
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return "General"


# مثال في FastAPI
@app.post("/api/vip/medical-tracking")
async def vip_medical_tracking(request: dict):
    patient_id = request.get("patient_id")
    user_input = request.get("symptoms")
    
    result = generate_vip_personalized_response(patient_id, user_input)
    return result


# ====================== VIP HEALTH SUMMARY & PERSONALIZED TRACKING ======================
@app.route('/api/patient/<int:patient_id>/vip-health-summary', methods=['GET'])
def get_vip_health_summary(patient_id):
    try:
        history = get_patient_history(str(patient_id))

        if not history:
            return jsonify({
                "has_history": False,
                "last_diagnosis": "غير محدد",
                "improvement_percentage": 0,
                "message": "ابدأ رحلة متابعتك الصحية مع المدرب الذكي"
            }), 200

        diagnosis = history.get('last_diagnosis') or history.get('last_specialty') or "غير محدد"
        severity = int(history.get('last_severity', 5))
        improvement = max(0, 100 - (severity * 10))

        return jsonify({
            "has_history": True,
            "last_diagnosis": diagnosis,
            "previous_severity": severity,
            "improvement_percentage": improvement,
            "last_symptoms": history.get('last_symptoms', ''),
            "recommended_specialty": history.get('last_specialty', 'طب عام'),
            "last_updated": history.get('timestamp', '')
        }), 200

    except Exception as e:
        print(f"Error in vip-health-summary: {e}")
        return jsonify({
            "has_history": False,
            "last_diagnosis": "غير محدد",
            "improvement_percentage": 0
        }), 500
    
@app.route('/api/vip-chat/<int:patient_id>/message', methods=['POST'])
def vip_medical_chat(patient_id):
    try:
        data = request.get_json() or {}
        user_input = data.get('message', '').strip()

        if not user_input:
            return jsonify({"error": "Message is required"}), 400

        print(f"🔥 VIP Chat → Patient {patient_id} | Message: {user_input[:100]}...")

        history = get_patient_history(str(patient_id))

        if not history:
            ai_response = "عذراً، لا يوجد سجل طبي سابق. يرجى وصف حالتك بالتفصيل حتى أتمكن من مساعدتك."
        else:
            try:
                result = generate_vip_personalized_response(str(patient_id), user_input)
                ai_response = result.get('ai_response') or result.get('response') or ""
                
                if not ai_response or len(ai_response.strip()) < 5:
                    print("⚠️ generate_vip_personalized_response returned empty response!")
                    ai_response = "شكراً لتحديثك. بناءً على تاريخك الطبي (Cardiology)، يُفضل استشارة الطبيب إذا استمرت الأعراض. هل يمكنك وصف المزيد من التفاصيل؟"
            except Exception as inner_e:
                print(f"❌ Error in generate_vip_personalized_response: {inner_e}")
                traceback.print_exc()
                ai_response = "حدث خطأ أثناء معالجة رد الذكاء الاصطناعي. حاول مرة أخرى."

        return jsonify({
            "success": True,
            "ai_response": ai_response,
            "reply": ai_response,          # ← Add this for frontend compatibility
            "message": ai_response,        # ← Add this too
            "language": "ar",
            "is_vip": True
        }), 200

    except Exception as e:
        print(f"❌ VIP Chat Error: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "ai_response": "عذراً، حدث خطأ في الخادم. يرجى المحاولة مرة أخرى.",
            "reply": "عذراً، حدث خطأ في الخادم. يرجى المحاولة مرة أخرى."
        }), 200


@app.route('/api/debug/followup-history', methods=['GET'])
def debug_followup_history():
    """للتصحيح فقط - تشوف كل البيانات المحفوظة في FollowUp_History"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM FollowUp_History ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append(dict(row))
            
            return jsonify({
                "count": len(data),
                "records": data
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    
if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
=======
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response"""
    origin = request.headers.get("Origin")
    allowed_origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

# ========== Global Error Handlers ==========

@app.errorhandler(400)
def bad_request_error(e):
    """Handle 400 Bad Request errors"""
    logger.error(f"Bad Request: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": "The request was invalid. Please check your input."
    }), 400

@app.errorhandler(401)
def unauthorized_error(e):
    """Handle 401 Unauthorized errors"""
    logger.error(f"Unauthorized: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": "Please login to access this resource."
    }), 401

@app.errorhandler(403)
def forbidden_error(e):
    """Handle 403 Forbidden errors"""
    logger.error(f"Forbidden: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Forbidden",
        "message": "You don't have permission to access this resource."
    }), 403

@app.errorhandler(404)
def not_found_error(e):
    """Handle 404 Not Found errors"""
    logger.error(f"Not Found: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Not found",
        "message": "The requested resource was not found."
    }), 404

@app.errorhandler(405)
def method_not_allowed_error(e):
    """Handle 405 Method Not Allowed errors"""
    logger.error(f"Method Not Allowed: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": f"The {request.method} method is not allowed for this endpoint."
    }), 405

@app.errorhandler(409)
def conflict_error(e):
    """Handle 409 Conflict errors"""
    logger.error(f"Conflict: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Conflict",
        "message": "The resource already exists or there is a conflict."
    }), 409

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 Internal Server errors"""
    logger.error(f"Internal Server Error: {str(e)}")
    traceback.print_exc()
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

# ========== Global Exception Handler ==========
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled Exception: {str(e)}")
    traceback.print_exc()
    
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

# ========== Request Logging Middleware ==========
@app.before_request
def log_request_info():
    """Log incoming request details for debugging"""
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        logger.info(f"📨 {request.method} {request.path} - Data: {request.get_json(silent=True)}")
    else:
        logger.info(f"📨 {request.method} {request.path} - Args: {dict(request.args)}")

@app.after_request
def log_response_info(response):
    """Log response status for debugging"""
    logger.info(f"📤 {request.method} {request.path} - Status: {response.status_code}")
    return response

# ========== Register Blueprints ==========
app.register_blueprint(auth_bp)
app.register_blueprint(doctors_bp)
app.register_blueprint(clinics_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(slots_bp)

logger.info("✅ All blueprints registered successfully")

# ========== Health Check Endpoints ==========
@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Medical Assistant API",
        "version": "1.0.0",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with database status"""
    try:
        from database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()["count"]
        
        return jsonify({
            "status": "healthy",
            "service": "Medical Assistant API",
            "version": "1.0.0",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "database": {
                "connected": True,
                "user_count": user_count
            },
            "blueprints": [
                "auth", "doctors", "clinics", "appointments",
                "reviews", "ai", "analytics", "slots"
            ]
        }), 200
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({
            "status": "degraded",
            "error": str(e),
            "database": {"connected": False}
        }), 500

# ========== API Info Endpoint ==========
@app.route('/api/info', methods=['GET'])
def api_info():
    """Get API information and available endpoints"""
    endpoints = {
        "auth": [
            "POST /api/signup",
            "POST /api/login"
        ],
        "doctors": [
            "GET /api/manager/doctors",
            "POST /api/manager/add-doctor",
            "GET /api/manager/doctor/<id>",
            "PUT /api/manager/doctor/<id>",
            "DELETE /api/manager/doctor/<id>",
            "GET /api/doctor/<id>/clinics",
            "GET /api/doctor/<id>/quick-stats"
        ],
        "clinics": [
            "GET /api/manager/clinics",
            "POST /api/manager/add-clinic",
            "PUT /api/manager/clinic/<id>",
            "DELETE /api/manager/clinic/<id>",
            "GET /api/clinics/<id>"
        ],
        "appointments": [
            "POST /api/appointments/book",
            "GET /api/patient/<id>/appointments",
            "PATCH /api/appointments/<id>/status",
            "POST /api/appointments/<id>/cancel"
        ],
        "reviews": [
            "GET /api/doctor/<id>/reviews",
            "POST /api/appointments/<id>/review",
            "PUT /api/reviews/<id>",
            "DELETE /api/reviews/<id>"
        ],
        "ai_chat": [
            "POST /chat",
            "POST /chat/specialty-only",
            "POST /api/vip-chat/<patient_id>/message",
            "GET /api/patient/<patient_id>/vip-health-summary"
        ],
        "analytics": [
            "GET /api/doctor/<id>/analytics",
            "GET /api/doctor/<id>/appointments/count",
            "GET /api/doctor/<id>/appointments/stats",
            "GET /api/manager/analytics"
        ],
        "slots": [
            "GET /api/doctor/<id>/available-slots",
            "POST /api/doctor/<id>/manual-slot",
            "PUT /api/doctor/<id>/available-slots/<slot_id>",
            "DELETE /api/doctor/<id>/available-slots/<slot_id>",
            "POST /api/doctor/<id>/generate-slots-range"
        ]
    }
    
    return jsonify({
        "success": True,
        "service": "Medical Assistant API",
        "version": "1.0.0",
        "endpoints": endpoints
    }), 200

# ========== Initialize Database ==========
try:
    init_database()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {str(e)}")
    traceback.print_exc()

# ========== Run App ==========
if __name__ == '__main__':
    logger.info("🚀 Starting Medical Assistant API Server...")
    logger.info("📍 Running on: http://localhost:5000")
    logger.info("📋 API Info: http://localhost:5000/api/info")
    logger.info("💚 Health Check: http://localhost:5000/health")
    
    app.run(
        debug=True, 
        port=5000, 
        threaded=True,
        host='0.0.0.0'  # Allow external connections
    )
>>>>>>> master
