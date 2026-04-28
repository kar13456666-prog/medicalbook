from flask import request, jsonify
from datetime import datetime, timezone
from database import get_db
from . import reviews_bp
import traceback
import sqlite3

@reviews_bp.route('/api/doctor/<int:doctor_id>/reviews', methods=['GET', 'OPTIONS'])
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

@reviews_bp.route('/api/appointments/<int:appointment_id>/review', methods=['POST'])
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

@reviews_bp.route('/api/reviews/<int:review_id>', methods=['PUT', 'DELETE'])
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


@reviews_bp.route('/api/appointments/<int:appointment_id>/can-review', methods=['GET'])
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
