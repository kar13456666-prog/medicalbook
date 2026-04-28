from flask import request, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from database import get_db
from . import doctors_bp
import json
import traceback

@doctors_bp.route('/api/manager/doctors', methods=['GET'])
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
                
                if doc_dict.get("clinic_affiliations"):
                    try:
                        doc_dict["clinic_affiliations"] = json.loads(doc_dict["clinic_affiliations"])
                    except:
                        doc_dict["clinic_affiliations"] = []
                else:
                    doc_dict["clinic_affiliations"] = []
                
                doc_dict["isSuspended"] = bool(doc_dict.get("isSuspended", 0))
                
                cleaned.append(doc_dict)
            
            return jsonify(cleaned), 200
            
    except Exception as e:
        print(f"Error in get_all_doctors: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@doctors_bp.route('/api/manager/add-doctor', methods=['POST'])
def add_doctor():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        required_fields = ["name", "email", "password", "specialty"]
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT _id FROM users WHERE email = ?", (data["email"],))
            if cursor.fetchone():
                return jsonify({"error": "Email already exists"}), 409

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
                "clinic_affiliations": "[]"  
            }

            clinic_id = data.get("clinic_id")
            if clinic_id:
                try:
                    clinic_id_int = int(clinic_id)  
                except:
                    return jsonify({"error": "Invalid clinic_id format"}), 400

                cursor.execute("SELECT _id FROM clinics WHERE _id = ?", (clinic_id_int,))
                if not cursor.fetchone():
                    return jsonify({"error": "Clinic not found"}), 404

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
                
                affiliations_list = [affiliation]
                new_doctor["clinic_affiliations"] = json.dumps(affiliations_list)

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


@doctors_bp.route('/api/manager/doctor/<int:doctor_id>', methods=['GET'])
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
            
            if doctor_dict.get("clinic_affiliations"):
                try:
                    doctor_dict["clinic_affiliations"] = json.loads(doctor_dict["clinic_affiliations"])
                except:
                    doctor_dict["clinic_affiliations"] = []
            else:
                doctor_dict["clinic_affiliations"] = []
            
            doctor_dict["isSuspended"] = bool(doctor_dict.get("isSuspended", 0))
            
            if doctor_dict.get("created_at"):
                doctor_dict["created_at"] = doctor_dict["created_at"]
            if doctor_dict.get("updated_at"):
                doctor_dict["updated_at"] = doctor_dict["updated_at"]
            
            return jsonify(doctor_dict), 200
            
    except Exception as e:
        print(f"Error in get_doctor_by_id: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@doctors_bp.route('/api/manager/doctor/<int:id>', methods=['PUT'])
def update_doctor(id):
    try:
        data = request.get_json()
        print("Received PUT data:", data)

        try:
            doc_id = int(id)  
        except Exception:
            return jsonify({"error": "Invalid doctor ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
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

            if "slot_duration" in data or "prices" in data:
                cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ?", (doc_id,))
                result = cursor.fetchone()
                affiliations = []
                
                if result and result["clinic_affiliations"]:
                    try:
                        affiliations = json.loads(result["clinic_affiliations"])
                    except:
                        affiliations = []
                
                if affiliations:
                    if "slot_duration" in data:
                        affiliations[0]["slot_duration"] = data["slot_duration"]
                    if "prices" in data:
                        affiliations[0]["prices"] = data["prices"]
                    
                    update_fields["clinic_affiliations"] = json.dumps(affiliations)

            if update_fields:
                update_fields["updated_at"] = datetime.utcnow().isoformat()
                
                set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
                update_values = list(update_fields.values())
                update_values.append(doc_id)
                
                query = f"UPDATE users SET {set_clause} WHERE _id = ?"
                cursor.execute(query, update_values)
                
                print(f"Modified count: {cursor.rowcount}")
                if cursor.rowcount == 0:
                    print("Warning: No fields were changed – data may be identical")

            cursor.execute("SELECT * FROM users WHERE _id = ?", (doc_id,))
            updated = cursor.fetchone()
            
            if updated:
                updated_dict = dict(updated)
                updated_dict["_id"] = updated_dict.pop("_id")
                
                if updated_dict.get("clinic_affiliations"):
                    try:
                        updated_dict["clinic_affiliations"] = json.loads(updated_dict["clinic_affiliations"])
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


@doctors_bp.route('/api/manager/doctor/<int:id>', methods=['DELETE'])
def delete_doctor(id):
    try:
        try:
            doc_id = int(id)  
        except Exception:
            return jsonify({"error": "Invalid doctor ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT _id FROM users WHERE _id = ? AND role = 'doctor'", (doc_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Doctor not found"}), 404

            cursor.execute("DELETE FROM appointments WHERE doctor_id = ?", (doc_id,))
            
            cursor.execute("DELETE FROM slots WHERE doctor_id = ?", (doc_id,))
            
            cursor.execute("DELETE FROM reviews WHERE doctor_id = ?", (doc_id,))
            
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


@doctors_bp.route('/api/doctor/<int:doctor_id>/clinics', methods=['GET'])
def get_doctor_clinics(doctor_id):
    """
    Get all active clinics where doctor works
    """
    try:
        doctor_id_int = int(doctor_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT clinic_affiliations FROM users WHERE _id = ? AND role = 'doctor'", (doctor_id_int,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({"error": "Doctor not found"}), 404
            
            doctor_data = dict(row)
            
            affiliations = []
            if doctor_data.get("clinic_affiliations"):
                try:
                    affiliations = json.loads(doctor_data["clinic_affiliations"])
                except Exception as e:
                    print(f"JSON Parse error: {e}")
                    affiliations = []
            
            active_clinic_ids = []
            for aff in affiliations:
                if aff.get("is_active", True):
                    clinic_id = aff.get("clinic_id")
                    if clinic_id:
                        active_clinic_ids.append(int(clinic_id))
            
            if not active_clinic_ids:
                return jsonify([]), 200
            
            placeholders = ','.join(['?'] * len(active_clinic_ids))
            cursor.execute(f'''
                SELECT _id, name, location, phone, image, rating 
                FROM clinics 
                WHERE _id IN ({placeholders})
            ''', active_clinic_ids)
            
            clinics_rows = cursor.fetchall()
            
            final_result = []
            for c_row in clinics_rows:
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
        traceback.print_exc() 
        return jsonify({"error": "Server error"}), 500
    
@doctors_bp.route('/api/doctor/<int:doctor_id>/quick-stats', methods=['GET'])
def get_doctor_quick_stats(doctor_id):
    try:
        doctor_id_int = int(doctor_id)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND date = ? AND status NOT IN ('cancelled', 'rejected')
            ''', (doctor_id_int, today))
            today_count = cursor.fetchone()["count"] or 0
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND status = 'pending'
            ''', (doctor_id_int,))
            pending_count = cursor.fetchone()["count"] or 0
            
            cursor.execute("SELECT rating, rating_count, clinic_affiliations FROM users WHERE _id = ?", (doctor_id_int,))
            doctor = cursor.fetchone()
            
            avg_rating = doctor["rating"] if doctor else 0
            
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
