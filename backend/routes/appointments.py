from flask import request, jsonify
from datetime import datetime, timedelta
from database import get_db
from . import appointments_bp
import traceback
import sqlite3


@appointments_bp.route('/api/appointments/book', methods=['POST'])
def book_appointment():
    """
    Book a new appointment
    Expected data: {
        "patient_id": int,
        "doctor_id": int, 
        "clinic_id": int,
        "date": "YYYY-MM-DD",
        "start_time": "HH:MM",
        "type": "consultation" or "follow_up",
        "duration_minutes": int (optional)
    }
    """
    try:
        data = request.json
        time_val = data.get("start_time") or data.get("time_slot")
        
        required = ["patient_id", "doctor_id", "clinic_id", "date", "type"]
        if not time_val or not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT price, type, duration_minutes FROM slots 
                WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ? 
                LIMIT 1
            ''', (data["doctor_id"], data["clinic_id"], data["date"], time_val))
            
            slot = cursor.fetchone()
            
            if not slot:
                return jsonify({"error": "Time slot not found or unavailable"}), 404
            
            price = float(slot["price"]) if slot and slot["price"] else 250.0
            
            if slot and slot["duration_minutes"]:
                duration = slot["duration_minutes"]
            else:
                duration = 30 if data.get("type") == "consultation" else 20
            
            try:
                start_dt = datetime.strptime(f"{data['date']} {time_val}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(minutes=duration)
                end_time = end_dt.strftime("%H:%M")
            except Exception as e:
                print(f"⚠️ Time calculation error: {e}, using same time as end_time")
                end_time = time_val
            
            if data.get("type") == "follow_up":
                price = price * 0.7
            
            cursor.execute('''
                SELECT _id FROM appointments 
                WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ? 
                AND status NOT IN ('cancelled')
            ''', (data["doctor_id"], data["clinic_id"], data["date"], time_val))
            
            if cursor.fetchone():
                return jsonify({"error": "This time slot is already booked"}), 409
            
            cursor.execute('''
                INSERT INTO appointments 
                (patient_id, doctor_id, clinic_id, date, start_time, end_time, type, 
                duration_minutes, status, price, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            ''', (
                data["patient_id"], 
                data["doctor_id"], 
                data["clinic_id"], 
                data["date"], 
                time_val,
                end_time,
                data["type"], 
                duration,
                price,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            appointment_id = cursor.lastrowid
            
            # Update slot status to booked
            cursor.execute('''
                UPDATE slots 
                SET status = 'booked', appointment_id = ?, updated_at = ?
                WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ?
            ''', (appointment_id, datetime.now().isoformat(), 
                data["doctor_id"], data["clinic_id"], data["date"], time_val))
            
            conn.commit()
            
            return jsonify({
                "success": True, 
                "message": "Appointment booked successfully",
                "appointment_id": appointment_id,
                "price": round(price, 2),
                "start_time": time_val,
                "end_time": end_time,
                "duration_minutes": duration
            }), 201
            
    except Exception as e:
        print(f"❌ Booking Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/appointments/<int:appointment_id>/cancel', methods=['POST', 'PATCH'])
def cancel_appointment(appointment_id):
    """
    Cancel an appointment
    """
    try:
        data = request.get_json() or {}
        cancel_reason = data.get('reason', 'Cancelled by user')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT doctor_id, clinic_id, date, start_time, status
                FROM appointments 
                WHERE _id = ?
            ''', (appointment_id,))
            
            appointment = cursor.fetchone()
            
            if not appointment:
                return jsonify({"error": "Appointment not found"}), 404
            
            if appointment["status"] == "cancelled":
                return jsonify({"error": "Appointment already cancelled"}), 400
            
            if appointment["status"] == "completed":
                return jsonify({"error": "Cannot cancel a completed appointment"}), 400
            
            cursor.execute('''
                UPDATE appointments 
                SET status = 'cancelled', updated_at = ?, notes = ?
                WHERE _id = ?
            ''', (datetime.utcnow().isoformat(), cancel_reason, appointment_id))
            
            cursor.execute('''
                UPDATE slots 
                SET status = 'available', appointment_id = NULL, updated_at = ?
                WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ?
            ''', (datetime.utcnow().isoformat(),
                appointment["doctor_id"], appointment["clinic_id"],
                appointment["date"], appointment["start_time"]))
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Appointment cancelled successfully"
            }), 200
            
    except Exception as e:
        print(f"❌ Cancel Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/patient/<int:patient_id>/appointments', methods=['GET', 'OPTIONS'])
@appointments_bp.route('/api/patient/<int:patient_id>/appointments', methods=['GET', 'OPTIONS'])
def get_patient_appointments(patient_id):
    """
    Get all appointments for a patient with doctor and clinic details
    Optional query params: ?status=completed&limit=10&page=1
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * limit
        
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
                    a.updated_at,
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
            '''
            params = [patient_id]
            
            if status_filter:
                query += " AND a.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY a.date DESC, a.start_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            count_query = "SELECT COUNT(*) as total FROM appointments WHERE patient_id = ?"
            count_params = [patient_id]
            if status_filter:
                count_query += " AND status = ?"
                count_params.append(status_filter)
            
            cursor.execute(count_query, count_params)
            total_result = cursor.fetchone()
            total = total_result["total"] if total_result else 0
            
            appointments = []
            for row in rows:
                apt = dict(row)
                
                apt["_id"] = str(apt["_id"])
                if apt.get("doctor_id"):
                    apt["doctor_id"] = str(apt["doctor_id"])
                if apt.get("clinic_id"):
                    apt["clinic_id"] = str(apt["clinic_id"])
                
                if not apt.get("doctor_name"):
                    apt["doctor_name"] = "Unknown Doctor"
                if not apt.get("clinic_name"):
                    apt["clinic_name"] = "Not specified"
                if not apt.get("price"):
                    apt["price"] = 0
                if not apt.get("duration_minutes"):
                    apt["duration_minutes"] = 30
                
                apt["notes"] = ""
                    
                appointments.append(apt)
            
            return jsonify({
                "success": True,
                "appointments": appointments,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 0
            }), 200
            
    except Exception as e:
        print(f"❌ Error in get_patient_appointments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/doctor/<int:doctor_id>/appointments/upcoming', methods=['GET'])
def get_doctor_upcoming_appointments(doctor_id):
    """
    Get upcoming appointments for a doctor
    """
    try:
        doctor_id_int = int(doctor_id)
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        
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
                    p._id as patient_id,
                    p.name as patient_name,
                    p.image as patient_image,
                    c._id as clinic_id,
                    c.name as clinic_name
                FROM appointments a
                LEFT JOIN users p ON a.patient_id = p._id
                LEFT JOIN clinics c ON a.clinic_id = c._id
                WHERE a.doctor_id = ? 
                AND a.status IN ('pending', 'confirmed')
                AND (
                    a.date > ? 
                    OR (a.date = ? AND a.start_time > ?)
                )
                ORDER BY a.date ASC, a.start_time ASC
                LIMIT 20
            '''
            
            cursor.execute(query, (doctor_id_int, today, today, current_time))
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                apt = dict(row)
                apt["_id"] = str(apt["_id"])
                if apt.get("patient_id"):
                    apt["patient_id"] = str(apt["patient_id"])
                if apt.get("clinic_id"):
                    apt["clinic_id"] = str(apt["clinic_id"])
                appointments.append(apt)
            
            return jsonify({
                "success": True,
                "appointments": appointments,
                "count": len(appointments)
            }), 200
            
    except Exception as e:
        print(f"❌ Error in get_doctor_upcoming_appointments: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/appointments/<int:appointment_id>/status', methods=['PATCH'])
def update_appointment_status(appointment_id):
    """
    Update appointment status
    Valid statuses: pending, confirmed, cancelled, completed, delayed
    """
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
            
            cursor.execute("SELECT status, doctor_id, clinic_id, date, start_time FROM appointments WHERE _id = ?", (appointment_id_int,))
            current = cursor.fetchone()
            
            if not current:
                return jsonify({"error": "Appointment not found"}), 404
            
            if new_status == 'cancelled' and current["status"] != 'cancelled':
                cursor.execute('''
                    UPDATE slots 
                    SET status = 'available', appointment_id = NULL, updated_at = ?
                    WHERE doctor_id = ? AND clinic_id = ? AND date = ? AND start_time = ?
                ''', (datetime.utcnow().isoformat(),
                      current["doctor_id"], current["clinic_id"],
                      current["date"], current["start_time"]))
            
            cursor.execute('''
                UPDATE appointments 
                SET status = ?, updated_at = ?
                WHERE _id = ?
            ''', (new_status, datetime.utcnow().isoformat(), appointment_id_int))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Appointment not found"}), 404

            conn.commit()
            
            return jsonify({
                "success": True, 
                "message": f"Status updated to {new_status}",
                "previous_status": current["status"],
                "new_status": new_status
            }), 200

    except ValueError:
        return jsonify({"error": "Invalid appointment ID format"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment_details(appointment_id):
    """
    Get detailed information about a specific appointment
    """
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
                    a.updated_at,
                    a.notes,
                    p._id as patient_id,
                    p.name as patient_name,
                    p.email as patient_email,
                    p.image as patient_image,
                    d._id as doctor_id,
                    d.name as doctor_name,
                    d.specialty as doctor_specialty,
                    d.image as doctor_image,
                    d.rating as doctor_rating,
                    c._id as clinic_id,
                    c.name as clinic_name,
                    c.location as clinic_location,
                    c.phone as clinic_phone
                FROM appointments a
                LEFT JOIN users p ON a.patient_id = p._id
                LEFT JOIN users d ON a.doctor_id = d._id
                LEFT JOIN clinics c ON a.clinic_id = c._id
                WHERE a._id = ?
            '''
            
            cursor.execute(query, (appointment_id,))
            appointment = cursor.fetchone()
            
            if not appointment:
                return jsonify({"error": "Appointment not found"}), 404
            
            apt_dict = dict(appointment)
            apt_dict["_id"] = str(apt_dict["_id"])
            if apt_dict.get("patient_id"):
                apt_dict["patient_id"] = str(apt_dict["patient_id"])
            if apt_dict.get("doctor_id"):
                apt_dict["doctor_id"] = str(apt_dict["doctor_id"])
            if apt_dict.get("clinic_id"):
                apt_dict["clinic_id"] = str(apt_dict["clinic_id"])
            
            return jsonify({
                "success": True,
                "appointment": apt_dict
            }), 200
            
    except Exception as e:
        print(f"❌ Error in get_appointment_details: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@appointments_bp.route('/api/appointments/check-availability', methods=['POST'])
def check_appointment_availability():
    """
    Check if a time slot is available before booking
    """
    try:
        data = request.get_json()
        required = ["doctor_id", "clinic_id", "date", "start_time"]
        
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if slot exists and is available
            cursor.execute('''
                SELECT s._id, s.type, s.price, s.duration_minutes, s.status,
                    CASE WHEN a._id IS NULL THEN 'available' ELSE 'booked' END as actual_status
                FROM slots s
                LEFT JOIN appointments a ON s.doctor_id = a.doctor_id 
                    AND s.clinic_id = a.clinic_id 
                    AND s.date = a.date 
                    AND s.start_time = a.start_time 
                    AND a.status != 'cancelled'
                WHERE s.doctor_id = ? 
                    AND s.clinic_id = ? 
                    AND s.date = ? 
                    AND s.start_time = ?
            ''', (data["doctor_id"], data["clinic_id"], data["date"], data["start_time"]))
            
            slot = cursor.fetchone()
            
            if not slot:
                return jsonify({
                    "available": False,
                    "reason": "Time slot not found in schedule"
                }), 200
            
            is_available = slot["actual_status"] == "available"
            
            return jsonify({
                "available": is_available,
                "slot_id": slot["_id"],
                "type": slot["type"],
                "price": float(slot["price"]) if slot["price"] else 0,
                "duration_minutes": slot["duration_minutes"]
            }), 200
            
    except Exception as e:
        print(f"❌ Error in check_appointment_availability: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500