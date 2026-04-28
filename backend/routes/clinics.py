from flask import request, jsonify
from datetime import datetime, timezone
from database import get_db
from . import clinics_bp
import json
import traceback

@clinics_bp.route('/api/manager/clinics', methods=['GET'])
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


@clinics_bp.route('/api/manager/add-clinic', methods=['POST'])
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
            "departments": json.dumps(data.get("departments", [])),  
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



@clinics_bp.route('/api/manager/clinic/<int:id>', methods=['PUT'])
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


@clinics_bp.route('/api/manager/clinic/<int:id>', methods=['DELETE'])
def delete_clinic(id):
    try:
        try:
            clinic_id = int(id)
        except:
            return jsonify({"error": "Invalid clinic ID format"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT _id FROM clinics WHERE _id = ?", (clinic_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Clinic not found"}), 404
            
            cursor.execute("DELETE FROM appointments WHERE clinic_id = ?", (clinic_id,))
            
            cursor.execute("DELETE FROM slots WHERE clinic_id = ?", (clinic_id,))
            
            cursor.execute("DELETE FROM clinics WHERE _id = ?", (clinic_id,))

        return jsonify({"message": "Clinic deleted successfully"}), 200
        
    except Exception as e:
        print(f"Error in delete_clinic: {str(e)}")
        return jsonify({"error": str(e)}), 500


@clinics_bp.route('/api/clinics/<int:clinic_id>', methods=['GET'])
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

            clinic_dict = dict(clinic)
            clinic_dict["id"] = clinic_dict.pop("_id")
            
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
