from flask import request, jsonify
from datetime import datetime, timedelta
from database import get_db
from . import slots_bp
import json
import traceback
import uuid


@slots_bp.route('/api/doctor/<int:doctor_id>/available-slots', methods=['GET'])
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


@slots_bp.route('/api/doctor/<int:doctor_id>/manual-slot', methods=['POST'])
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


@slots_bp.route('/api/doctor/<int:doctor_id>/available-slots/<int:slot_id>', methods=['PUT'])
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


@slots_bp.route('/api/doctor/<int:doctor_id>/available-slots/<int:slot_id>', methods=['DELETE'])
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


@slots_bp.route('/api/doctor/<int:doctor_id>/generate-slots-range', methods=['POST'])
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


# ========== WEEKLY SCHEDULE MANAGEMENT ==========

@slots_bp.route('/api/doctor/<int:doctor_id>/clinics/<int:clinic_id>/weekly-schedule', methods=['GET'])
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


@slots_bp.route('/api/doctor/<int:doctor_id>/clinics/<int:clinic_id>/weekly-schedule', methods=['POST'])
def add_weekly_schedule_slot(doctor_id, clinic_id):
    """
    Add a new slot to weekly schedule
    """
    try:
        data = request.get_json()
        required = ["day", "start_time", "end_time"]
        
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing required fields: {required}"}), 400
        
        doctor_id_int = int(doctor_id)
        clinic_id_int = int(clinic_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get doctor's affiliations
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
            
            # Find the affiliation
            affiliation_index = None
            for i, aff in enumerate(affiliations):
                if aff.get("clinic_id") == clinic_id_int:
                    affiliation_index = i
                    break

            if affiliation_index is None:
                return jsonify({"error": "Doctor not affiliated with this clinic"}), 403

            # Create new slot with UUID
            new_slot = {
                "_id": str(uuid.uuid4()),
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

    except Exception as e:
        print(f"Error in add_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@slots_bp.route('/api/doctor/<int:doctor_id>/clinics/<int:clinic_id>/weekly-schedule/<string:slot_id>', methods=['PUT'])
def update_weekly_schedule_slot(doctor_id, clinic_id, slot_id):
    """
    Update an existing slot in weekly schedule
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
                    if "day" in data:
                        slot["day"] = data["day"]
                    if "start_time" in data:
                        slot["start_time"] = data["start_time"]
                    if "end_time" in data:
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

    except Exception as e:
        print(f"Error in update_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@slots_bp.route('/api/doctor/<int:doctor_id>/clinics/<int:clinic_id>/weekly-schedule/<string:slot_id>', methods=['DELETE'])
def delete_weekly_schedule_slot(doctor_id, clinic_id, slot_id):
    """
    Delete a slot from weekly schedule
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

    except Exception as e:
        print(f"Error in delete_weekly_schedule_slot: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@slots_bp.route('/api/doctor/<int:doctor_id>/clinics/<int:clinic_id>/affiliate', methods=['POST'])
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