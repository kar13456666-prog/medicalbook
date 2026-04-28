from flask import request, jsonify
from database import get_db
from rag_openai import (
    generate_medical_response, detect_language, check_intent_with_llm,
    generate_dynamic_response_with_llm, generate_vip_personalized_response,
    get_patient_history, build_conversation_context, map_to_app_specialty
)
from . import ai_bp
import traceback
import sqlite3


@ai_bp.route('/chat', methods=['POST', 'OPTIONS'])
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

        conversation_context = build_conversation_context(history, user_message)

        result = generate_dynamic_response_with_llm(conversation_context, user_message, history)

        print(f"✅ Dynamic LLM decided: type = {result.get('type', 'unknown')} | Message: '{user_message[:60]}...'")

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

        if response_type == "doctor_request":
            specialty = None
            
            if isinstance(analysis, dict):
                specialty = analysis.get('specialty')
            
            if not specialty and isinstance(result, dict):
                specialty = result.get('recommended_specialty')
            
            if not specialty and isinstance(result, dict):
                specialty = result.get('specialty_detected')
            
            if not specialty:
                specialty = extract_specialty_from_message(user_message)
            
            if not specialty:
                specialty = "Internal Medicine"
            
            normalized_specialty = map_to_app_specialty(specialty)
            
            print(f"🎯 Extracted specialty: '{specialty}' → Normalized: '{normalized_specialty}'")

            response_data.update({
                "type": "doctor_request",
                "recommended_specialty": normalized_specialty,
                "original_specialty": specialty,  
                "show_doctors": True,
                "ai_response": ai_response,
                "response": ai_response,
                "reply": ai_response,
                "message": f"{ai_response}\n\nهل تريد رؤية الدكاترة المتاحين في تخصص **{normalized_specialty}**؟"
            })

        elif response_type == "medical" and isinstance(analysis, dict):
            specialty = analysis.get('specialty')
            
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
    

@ai_bp.route('/chat/specialty-only', methods=['POST'])
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


@ai_bp.route('/api/vip-chat/<int:patient_id>/message', methods=['POST'])
def vip_medical_tracking(patient_id):
    """
    VIP chat endpoint for personalized medical follow-up
    Accepts patient_id from URL and message from request body
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided",
                "ai_response": "يرجى إرسال رسالة تحتوي على الأعراض التي تعاني منها."
            }), 400
        
        user_input = data.get('message') or data.get('symptoms')
        
        if not user_input:
            return jsonify({
                "success": False,
                "error": "Message or symptoms field is required",
                "ai_response": "يرجى كتابة الأعراض التي تعاني منها لمتابعة حالتك."
            }), 400
        
        print(f"\n👑 VIP Chat - Patient {patient_id}")
        print(f"📨 Message: '{user_input[:100]}...'")
        
        result = generate_vip_personalized_response(str(patient_id), user_input)
        
        ai_response = result.get('ai_response') or result.get('response') or "شكراً لمتابعتك. هل يمكنك وصف الأعراض بمزيد من التفصيل؟"
        
        return jsonify({
            "success": result.get('success', True),
            "ai_response": ai_response,
            "reply": ai_response,
            "message": ai_response,
            "language": result.get('language', 'ar'),
            "is_vip": True,
            "patient_id": patient_id,
            "analysis": result.get('analysis', {})
        }), 200
        
    except Exception as e:
        print(f"❌ VIP Chat Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "ai_response": "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.",
            "reply": "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.",
            "type": "error",
            "is_vip": True
        }), 200


@ai_bp.route('/api/patient/<int:patient_id>/vip-health-summary', methods=['GET'])
def get_vip_health_summary(patient_id):
    """Get VIP health summary for a patient"""
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
        traceback.print_exc()
        return jsonify({
            "has_history": False,
            "last_diagnosis": "غير محدد",
            "improvement_percentage": 0,
            "error": str(e)
        }), 500


def extract_specialty_from_message(message):
    """استخراج التخصص من الرسالة النصية"""
    if not message:
        return None
    
    message_lower = message.lower()
    
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
        "Infectious Disease": ["معدية", "infectious", "infection", "virus"],
        "Respiratory Medicine": ["صدر", "respiratory", "lung", "chest", "صدرية", "كحة", "كحه"],
        "Gastroenterology": ["جهاز هضمي", "gastroenterology", "stomach", "digest", "قولون"],
        "Urology": ["مسالك بولية", "urology", "urinary", "kidney"]
    }
    
    for specialty, keywords in specialty_patterns.items():
        for keyword in keywords:
            if keyword in message_lower:
                print(f"🔍 Extracted '{specialty}' from message using keyword '{keyword}'")
                return specialty
    
    return None