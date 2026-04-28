from flask import request, jsonify
from database import get_db
from . import analytics_bp
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import calendar
import traceback
import json


@analytics_bp.route('/api/doctor/<int:doctor_id>/analytics', methods=['GET'])
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



@analytics_bp.route('/api/doctor/<int:doctor_id>/appointments/count', methods=['GET'])
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


@analytics_bp.route('/api/doctor/<int:doctor_id>/appointments/stats', methods=['GET'])
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

@analytics_bp.route('/api/manager/analytics', methods=['GET'])
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

@analytics_bp.route('/api/doctor/<int:doctor_id>/all-appointments', methods=['GET'])
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



@analytics_bp.route('/api/doctor/<int:doctor_id>/appointments/today', methods=['GET'])
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
