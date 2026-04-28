from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from database import get_db
from . import auth_bp
import traceback
import sqlite3


@auth_bp.route('/api/signup', methods=['POST'])
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
    

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
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
