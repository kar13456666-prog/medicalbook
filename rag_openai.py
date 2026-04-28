

import os
import sqlite3
import requests
import json
import re
from contextlib import contextmanager
from deep_translator import GoogleTranslator
import chromadb
from chromadb.utils import embedding_functions

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, CHROMA_PATH, DATABASE_PATH
from database import get_db, init_database

path = CHROMA_PATH

print("🔌 Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path=os.path.join(path, "medical_vector_db"))  

ef = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="medical_assistant", 
    embedding_function=ef
)
print("✅ Connected successfully to ChromaDB!")


translator = GoogleTranslator()


def detect_language(text):
    """Detect if text is Arabic or English"""
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    
    if arabic_pattern.search(text):
        return 'arabic'
    else:
        return 'english'

def translate_to_english(text):
    """Translate Arabic text to English for vector search"""
    try:
        translated = translator.translate(text, dest='en')
        print(f"   🔄 Internal translation: '{text[:50]}...' → '{translated[:50]}...'")
        return translated
    except Exception as e:
        print(f"   ⚠️ Translation failed: {e}, using original text")
        return text

def is_greeting_or_non_medical(text, language):
    """Check if user input is just a greeting or non-medical text"""
    
    arabic_non_medical = [
        'اهلا', 'أهلا', 'مرحبا', 'سلام', 'شكرا', 'شكراً', 'الله', 'كيف', 
        'الحال', 'اخبارك', 'صباح', 'مساء', 'بخير', 'تمام', 'حلو', 
        'ماشي', 'طيب', 'نعم', 'لا', 'اه', 'ايوه', 'هلا', 'هلا والله',
        'يعطيك العافية', 'يعطيكم العافية', 'حياك', 'الله يسلمك'
    ]
    
    english_non_medical = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'how are you', 'fine', 'ok', 'okay', 'yes', 'no',
        'good', 'bad', 'well', 'great', 'awesome', 'salam', 'ahlan', 'hey there',
        'whats up', 'howdy', 'greetings', 'yo', 'sup'
    ]
    
    text_lower = text.lower().strip()
    
    if language == 'arabic':
        words = text_lower.split()
        if len(words) <= 3: 
            for greeting in arabic_non_medical:
                if greeting in text_lower:
                    return True
    else:
        words = text_lower.split()
        if len(words) <= 3:  
            for greeting in english_non_medical:
                if greeting in text_lower:
                    return True
    
    return False

def get_greeting_response(language):
    """Return a friendly greeting response without searching database"""
    
    if language == 'arabic':
        return """أهلاً بك! 👋

أنا المساعد الطبي الذكي. أنا هنا لمساعدتك في:
• تحليل الأعراض الأولية
• اقتراح التخصص الطبي المناسب
• توجيهك للحجز في العيادة المناسبة

يرجى كتابة الأعراض التي تعاني منها بالتفصيل، مثل:
• "عندي صداع شديد مع غثيان"
• "عندي طفح جلدي وحكة"
• "ألم في الصدر وصعوبة في التنفس"

كيف يمكنني مساعدتك اليوم؟"""
    
    else:
        return """Welcome! 👋

I'm your AI medical assistant. I'm here to help you with:
• Preliminary symptom analysis
• Suggesting the right medical specialty
• Guiding you to book an appointment

Please describe your symptoms in detail, for example:
• "I have a severe headache with nausea"
• "I have a skin rash and itching"
• "Chest pain and difficulty breathing"

How can I help you today?"""

def get_system_prompt(language):
    if language == 'arabic':
        return """أنت مساعد طبي محترف يعمل في منصة حجز عيادات.
ردودك دقيقة، متعاطفة، ومهنية.
تحدث باللغة العربية الفصحى.
قدم نصائح طبية أولية فقط، ولا تقدم تشخيصاً نهائياً."""
    else:
        return """You are a professional medical assistant working for a clinic booking platform.
Your responses are accurate, empathetic, and professional.
Provide preliminary medical guidance only, no definitive diagnosis."""

def get_response_prompt(language, context, disease, severity, specialty, urgency, emergency_warning, user_input, conversation_context=None):
    """
    Build the prompt for AI based on detected language.
    
    Args:
        language: 'arabic' or 'english'
        context: Retrieved medical information from vector DB
        disease: Potential disease name
        severity: Severity score (0-10)
        specialty: Recommended medical specialty (in English)
        urgency: Urgency description
        emergency_warning: Boolean for emergency status
        user_input: Original user message
        conversation_context: Optional conversation history for context
    """
    
    context_section = ""
    if conversation_context:
        if language == 'arabic':
            context_section = f"""
**سياق المحادثة السابقة:**
{conversation_context}

"""
        else:
            context_section = f"""
**Conversation Context:**
{conversation_context}

"""
    
    if language == 'arabic':
        emergency_text = ""
        if emergency_warning:
            emergency_text = f"""
🚨 **تحذير عاجل!** 🚨
{urgency}
المرض المحتمل: {disease}

⚠️ هذه حالة طارئة تحتاج تدخل طبي فوري!
"""
        
        severity_desc = ""
        if severity >= 9:
            severity_desc = "🔴 حرجة جداً - طوارئ"
        elif severity >= 7:
            severity_desc = "🟠 عالية - مراجعة عاجلة"
        elif severity >= 4:
            severity_desc = "🟡 متوسطة - مراجعة قريبة"
        else:
            severity_desc = "🟢 بسيطة - متابعة"
        
        return f"""أنت مساعد طبي ذكي يعمل في منصة حجز عيادات.
{context_section}
**المعلومات الطبية المسترجعة:**
{context}

**تحليل الحالة:**
- المرض المحتمل: {disease}
- درجة الخطورة: {severity}/10 ({severity_desc})
- التخصص المطلوب (بالإنجليزية): {specialty}
- حالة الطوارئ: {emergency_text if emergency_text else '✅ لا توجد حالة طوارئ'}

**شكوى المستخدم:** "{user_input}"

**المطلوب منك:**
1. قم بالرد باللغة العربية الفصحى
2. اذكر المرض المحتمل بناءً على المعلومات المقدمة
3. **هام جداً:** عند ذكر التخصص الطبي في ردك، استخدم الاسم الإنجليزي (مثل "Infectious Disease" أو "Cardiology" أو "Pediatrics") حتى لو كان باقي الرد بالعربي
4. مثال على الرد الصحيح: "أنصحك بمراجعة طبيب في قسم **Cardiology** لأن أعراضك تشير إلى مشكلة في القلب"
5. إذا كانت درجة الخطورة 7 أو أكثر، ابدأ الرد بتحذير واضح
6. أضف التنويه الإلزامي: "تنبيه: هذا الاستبيان أولي فقط ولا يغني عن استشارة الطبيب المختص."
7. كن متعاطفاً ومهنياً في ردك
8. لا تقدم تشخيصاً نهائياً، فقط توجيهات أولية
9. إذا كان المستخدم يسأل عن الحجز، وجهه لاستخدام زر الحجز الموجود

**الرد:**"""
    
    else:
        emergency_text = ""
        if emergency_warning:
            emergency_text = f"""
🚨 **URGENT WARNING!** 🚨
{urgency}
Potential condition: {disease}

⚠️ This is an emergency that requires immediate medical attention!
"""
        
        severity_desc = ""
        if severity >= 9:
            severity_desc = "🔴 CRITICAL - Emergency"
        elif severity >= 7:
            severity_desc = "🟠 HIGH - Urgent care needed"
        elif severity >= 4:
            severity_desc = "🟡 MODERATE - Schedule soon"
        else:
            severity_desc = "🟢 LOW - Monitor symptoms"
        
        return f"""You are an intelligent medical assistant working for a clinic booking platform.
{context_section}
**Retrieved Medical Information:**
{context}

**Case Analysis:**
- Potential Condition: {disease}
- Severity Level: {severity}/10 ({severity_desc})
- Recommended Specialty: {specialty}
- Emergency Status: {emergency_text if emergency_text else '✅ No emergency detected'}

**User Symptoms:** "{user_input}"

**Instructions:**
1. Respond in English
2. Mention the potential condition based on the provided information
3. Advise the user to consult a doctor in the {specialty} department
4. If severity is 7 or higher, start the response with a clear warning
5. Include this mandatory disclaimer: "Disclaimer: This is a preliminary assessment only and does not replace professional medical advice. Please consult a qualified healthcare provider for proper diagnosis."
6. Be empathetic and professional in your response
7. Do not provide definitive diagnosis, only preliminary guidance
8. If the user asks about booking, direct them to use the booking button

**Response:**"""


def get_response_prompt_simple(language, context, disease, severity, specialty, urgency, emergency_warning, user_input):
    """
    Simplified version without conversation context
    """
    return get_response_prompt(language, context, disease, severity, specialty, urgency, emergency_warning, user_input, conversation_context=None)

def get_specialty_arabic(specialty):
    arabic_names = {
        'Dermatology': 'جلدية',
        'Neurology': 'مخ وأعصاب',
        'Internal Medicine': 'باطنة',
        'Cardiology': 'قلبية',
        'Gastroenterology': 'جهاز هضمي',
        'Respiratory Medicine': 'صدرية',
        'Orthopedics': 'عظام',
        'Urology': 'مسالك بولية',
        'Ophthalmology': 'عيون',
        'ENT': 'أنف وأذن وحنجرة',
        'Psychiatry': 'نفسية',
        'Infectious Disease': 'أمراض معدية',
        'General Medicine': 'طب عام',
    }
    return arabic_names.get(specialty, 'طب عام')

def map_to_app_specialty(ai_detected):
    """Convert AI detected specialty to match app's dropdown options"""
    if not ai_detected:
        return "Internal Medicine"
    
    val = ai_detected.lower().strip()
    
    mapping = {
        "pediatric": "Pediatrics",
        "pediatrics": "Pediatrics",
        "أطفال": "Pediatrics",
        "اطفال": "Pediatrics",
        "child": "Pediatrics",
        "baby": "Pediatrics",
        "kid": "Pediatrics",
        
        "internal medicine": "Internal Medicine",
        "internal": "Internal Medicine",
        "باطنة": "Internal Medicine",
        "طب باطني": "Internal Medicine",
        
        "cardiology": "Cardiology",
        "قلب": "Cardiology",
        "heart": "Cardiology",
        "chest pain": "Cardiology",
        
        "dermatology": "Dermatology",
        "جلدية": "Dermatology",
        "skin": "Dermatology",
        "rash": "Dermatology",
        
        "orthopedics": "Orthopedics",
        "orthopedic": "Orthopedics",
        "عظام": "Orthopedics",
        "bone": "Orthopedics",
        "joint": "Orthopedics",
        
        "ent": "ENT",
        "ear nose throat": "ENT",
        "أنف وأذن": "ENT",
        "ear": "ENT",
        "throat": "ENT",
        
        "neurology": "Neurology",
        "مخ وأعصاب": "Neurology",
        "brain": "Neurology",
        "nerve": "Neurology",
        "headache": "Neurology",
        "migraine": "Neurology",
        
        "ophthalmology": "Ophthalmology",
        "eye": "Ophthalmology",
        "عيون": "Ophthalmology",
        "vision": "Ophthalmology",
        
        "urology": "Urology",
        "مسالك بولية": "Urology",
        "urinary": "Urology",
        
        "gastroenterology": "Gastroenterology",
        "جهاز هضمي": "Gastroenterology",
        "stomach": "Gastroenterology",
        "digest": "Gastroenterology",
        
        "respiratory": "Respiratory Medicine",
        "chest": "Respiratory Medicine",
        "lung": "Respiratory Medicine",
        "صدرية": "Respiratory Medicine",
        "cough": "Respiratory Medicine",
        
        "psychiatry": "Psychiatry",
        "نفسية": "Psychiatry",
        "mental": "Psychiatry",
        "anxiety": "Psychiatry",
        "depression": "Psychiatry",
        
        "infectious": "Infectious Disease",
        "infection": "Infectious Disease",
        "أمراض معدية": "Infectious Disease",
        "bacteria": "Infectious Disease",
        "virus": "Infectious Disease",
        
        "general medicine": "General Medicine",
        "general": "General Medicine",
        "طب عام": "General Medicine",
        "family medicine": "General Medicine",
    }
    
    for key, target in mapping.items():
        if key in val:
            print(f"🔄 Mapping: '{ai_detected}' → '{target}'")
            return target
    
    print(f"⚠️ No mapping found for '{ai_detected}', defaulting to Internal Medicine")
    return "Internal Medicine"




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
    
    prompt = get_response_prompt_with_context(
        user_language, context, disease, severity, 
        specialty_display, urgency, emergency_warning, 
        original_message, full_context
    )
    
    print("🤖 Generating response with AI...")
    ai_response = call_openrouter(prompt, user_language)
    
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


def get_response_prompt_with_context(language, context, disease, severity, specialty, urgency, emergency_warning, user_input, full_context):
    """Build prompt with conversation context - uses get_response_prompt from rag_openai"""
    base_prompt = get_response_prompt(
        language, context, disease, severity, 
        specialty, urgency, emergency_warning, user_input
    )
    
    if full_context:
        if language == 'arabic':
            context_section = f"\n\n**سياق المحادثة السابقة:**\n{full_context}\n"
        else:
            context_section = f"\n\n**Conversation Context:**\n{full_context}\n"
        
        lines = base_prompt.split('\n')
        if language == 'arabic':
            insert_pos = 2 
        else:
            insert_pos = 2
        lines.insert(insert_pos, context_section)
        return '\n'.join(lines)
    
    return base_prompt

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



def get_urgency_arabic(score):
    if score >= 9:
        return "🚨 حالة خطيرة جداً - يجب التوجه للطوارئ فوراً!"
    elif score >= 7:
        return "⚠️ حالة عالية الخطورة - يجب مراجعة الطبيب خلال 24 ساعة"
    elif score >= 4:
        return "🟡 حالة متوسطة - يفضل مراجعة الطبيب خلال أسبوع"
    else:
        return "🟢 حالة بسيطة - يمكن مراقبة الأعراض مع استشارة الطبيب عند الحاجة"

def get_urgency_english(score):
    if score >= 9:
        return "🚨 CRITICAL EMERGENCY - Immediate medical attention required! Call ambulance now!"
    elif score >= 7:
        return "⚠️ HIGH URGENCY - See a doctor within 24 hours"
    elif score >= 4:
        return "🟡 MODERATE URGENCY - Schedule an appointment within a week"
    else:
        return "🟢 LOW URGENCY - Monitor symptoms, consult if persists"


print("🔌 Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path=os.path.join(path, "medical_vector_db"))  
ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_collection(name="medical_assistant", embedding_function=ef)  
print("✅ Connected successfully!")

class OpenRouterClient:
    """Client for OpenRouter API calls"""
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.chat = self  
    
    def completions(self):
        return self
    
    def create(self, **kwargs):
        """Create chat completion"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Medical Assistant RAG System",
        }
        
        payload = {
            "model": kwargs.get("model", "openai/gpt-4o"),
            "messages": kwargs.get("messages", []),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 500)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 30)
            )
            
            if response.status_code == 200:
                class Response:
                    def __init__(self, data):
                        self.choices = [Choice(data['choices'][0])]
                
                class Choice:
                    def __init__(self, data):
                        self.message = Message(data['message'])
                
                class Message:
                    def __init__(self, data):
                        self.content = data['content']
                
                return Response(response.json())
            else:
                raise Exception(f"API Error: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"OpenRouter Error: {str(e)}")

ai_client = OpenRouterClient(OPENROUTER_API_KEY, OPENROUTER_BASE_URL)
def smart_medical_query(user_input, original_language, n_results=3):
    """
    Query the vector database.
    If input is Arabic, it's internally translated to English for better search accuracy.
    """
    
    if original_language == 'arabic':
        search_query = translate_to_english(user_input)
    else:
        search_query = user_input
    
    results = collection.query(
        query_texts=[search_query],
        n_results=n_results
    )
    
    max_severity = 0
    most_critical_doc = None
    
    for i, metadata in enumerate(results['metadatas'][0]):
        severity = metadata.get('severity_score', 0)
        if severity > max_severity:
            max_severity = severity
            most_critical_doc = {
                'disease': metadata['disease'],
                'severity': severity,
                'specialty': metadata['specialty'],
                'text': results['documents'][0][i]
            }
    
    emergency_alert = None
    if max_severity >= 7:
        emergency_alert = {
            'disease': most_critical_doc['disease'],
            'severity_score': max_severity
        }
    
    return {
        'results': results,
        'max_severity': max_severity,
        'most_critical': most_critical_doc,
        'emergency_alert': emergency_alert,
        'recommended_specialty': most_critical_doc['specialty'] if most_critical_doc else 'General Medicine',
        'search_query_used': search_query  
    }

def call_openrouter(prompt, language):
    """Call OpenRouter API with the selected model"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Medical Assistant RAG System",
    }
    
    system_prompt = get_system_prompt(language)
    
    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API Error: {response.status_code}"
    
    except Exception as e:
        return f"Error: {str(e)}"
    



from typing import Literal
import functools
import time
import requests

IntentType = Literal["greeting", "medical"]

@functools.lru_cache(maxsize=1000)
def check_intent_with_llm(
    user_text: str,
    model: str = "openrouter/google/gemini-2.0-flash-001",
    retry_count: int = 2,
    timeout: int = 5
) -> IntentType:
    """
    Detect intent of user input using LLM with retry logic and validation.
    IMPORTANT: This analyzes ONLY the current message, not conversation history.
    
    Returns:
        "greeting" - if the message is a pure greeting or social talk
        "medical" - if the message contains symptoms, health concerns, or medical questions
    """
    
    user_text = user_text.strip()
    if not user_text:
        print("⚠️ Empty input received, defaulting to medical")
        return "medical"
    

    pure_greetings_ar = [
        'اهلا', 'أهلا', 'مرحبا', 'سلام', 'هلا', 'أهلاً', 'مرحباً',
        'عامل اي', 'عامل ايه', 'اخبارك', 'كيفك', 'كيف الحال',
        'صباح الخير', 'مساء الخير', 'حياك الله', 'الله يسلمك',
        'يعطيك العافية', 'شكرا', 'شكراً', 'تمام', 'بخير', 'الحمدلله',
        'الحمد لله', 'الحمدلله', 'ممتاز', 'كويس'
    ]
    
    pure_greetings_en = [
        'hello', 'hi', 'hey', 'greetings', 'howdy', 'sup',
        'good morning', 'good afternoon', 'good evening',
        'how are you', 'how do you do', 'nice to meet you',
        'thanks', 'thank you', 'welcome', 'fine', 'good',
        'great', 'awesome', 'cool', 'okay', 'ok'
    ]
    
    strong_medical_ar = [
        'وجع', 'ألم', 'الم', 'دواء', 'علاج', 'مرض', 'كحة', 'كحه',
        'حرارة', 'سخونية', 'تعب', 'إعياء', 'اعراض', 'أعراض',
        'مستشفى', 'عيادة', 'دكتور', 'طبيب', 'صحي', 'صحية',
        'جراحة', 'عملية', 'إسعاف', 'طوارئ', 'نزيف', 'كسور',
        'غثيان', 'قيء', 'اسهال', 'امساك', 'صداع', 'دوخة', 'دوار'
    ]
    
    strong_medical_en = [
        'pain', 'ache', 'sore', 'hurt', 'medicine', 'medication',
        'treatment', 'disease', 'illness', 'cough', 'fever',
        'temperature', 'fatigue', 'tired', 'symptom', 'hospital',
        'clinic', 'doctor', 'physician', 'surgery', 'operation',
        'emergency', 'bleeding', 'fracture', 'broken', 'infection',
        'nausea', 'vomiting', 'diarrhea', 'constipation', 'headache',
        'dizzy', 'dizziness', 'migraine', 'seizure', 'rash'
    ]
    
    user_lower = user_text.lower()
    word_count = len(user_text.split())
    

    if word_count <= 2:
        for greeting in pure_greetings_ar:
            if greeting in user_lower:
                has_medical = any(med in user_lower for med in strong_medical_ar)
                if not has_medical:
                    print(f"✅ Pure greeting detected (short message): '{user_text}'")
                    return "greeting"
        
        for greeting in pure_greetings_en:
            if greeting in user_lower:
                has_medical = any(med in user_lower for med in strong_medical_en)
                if not has_medical:
                    print(f"✅ Pure greeting detected (short message): '{user_text}'")
                    return "greeting"
    

    for keyword in strong_medical_ar + strong_medical_en:
        if keyword in user_lower:
            print(f"✅ Strong medical keyword detected: '{keyword}' in '{user_text}'")
            return "medical"
    

    has_greeting = any(g in user_lower for g in pure_greetings_ar + pure_greetings_en)
    has_medical = any(m in user_lower for m in strong_medical_ar + strong_medical_en)
    
    if has_greeting and has_medical:
        print(f"✅ Mixed content detected (greeting + medical): '{user_text}' → medical")
        return "medical"
    

    if word_count <= 3:
        all_greetings = True
        words = user_lower.split()
        for word in words:
            is_greeting_word = (
                word in pure_greetings_ar or 
                word in pure_greetings_en or
                word in ['ahla', 'ahlan', 'marhaba', 'salam', 'hello', 'hi', 'hey']
            )
            if not is_greeting_word:
                all_greetings = False
                break
        
        if all_greetings:
            print(f"✅ All words are greetings: '{user_text}' → greeting")
            return "greeting"
    

    for attempt in range(retry_count + 1):
        try:
            system_prompt = (
                "You are a strict intent classifier for a medical assistant chatbot.\n"
                "Analyze ONLY the user's CURRENT message (ignore any previous conversation).\n"
                "Output exactly one word in lowercase:\n\n"
                "Output 'greeting' ONLY if the message is PURELY a greeting or social talk like:\n"
                "• 'hello', 'hi', 'hey', 'good morning', 'how are you', 'what's up'\n"
                "• 'اهلا', 'مرحبا', 'سلام', 'كيف الحال', 'عامل ايه', 'اخبارك', 'شكرا'\n\n"
                "Output 'medical' if the message contains ANY of these:\n"
                "• Symptoms (pain, fever, cough, headache, nausea)\n"
                "• Health questions ('what causes', 'how to treat')\n"
                "• Medication or treatment mentions\n"
                "• Body parts (stomach, chest, head, throat)\n"
                "• Medical concerns or descriptions of illness\n\n"
                "IMPORTANT RULES:\n"
                "1. If the user says 'hello' or 'اهلا' alone → 'greeting'\n"
                "2. If the user says 'hello, I have a headache' → 'medical'\n"
                "3. If the message contains ANY medical term → 'medical'\n"
                "4. If you are unsure or the message is mixed → 'medical' (safety first)\n"
                "5. Do NOT output any other words, punctuation, or explanation\n"
                "6. Output ONLY 'greeting' or 'medical'"
            )
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Medical Assistant RAG System",
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}  
                ],
                "max_tokens": 5,
                "temperature": 0,  
                "top_p": 1.0
            }
            
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                intent = response.json()['choices'][0]['message']['content'].strip().lower()
                intent = intent.strip('.,!?;:')
                
                if intent == "greeting":
                    print(f"✅ LLM classified as greeting: '{user_text}'")
                    return "greeting"
                elif intent == "medical":
                    print(f"✅ LLM classified as medical: '{user_text}'")
                    return "medical"
                else:
                    print(f"⚠️ Attempt {attempt + 1}: Unexpected intent: '{intent}', defaulting to medical")
                    if attempt == retry_count:
                        return "medical"
                    continue
            else:
                print(f"⚠️ Attempt {attempt + 1}: API Error {response.status_code}")
                if attempt == retry_count:
                    return "medical"
                    
        except TimeoutError:
            print(f"⚠️ Attempt {attempt + 1}: Timeout")
            if attempt == retry_count:
                return "medical"
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}: Error: {e}")
            if attempt == retry_count:
                return "medical"
            time.sleep(0.5)
    
    print(f"⚠️ Defaulting to medical for: '{user_text}'")
    return "medical"


def clear_intent_cache():
    """Clear the intent classification cache"""
    check_intent_with_llm.cache_clear()
    print("✅ Intent cache cleared")


def get_intent_cache_stats():
    """Get cache performance statistics"""
    cache_info = check_intent_with_llm.cache_info()
    return {
        'hits': cache_info.hits,
        'misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize
    }


def is_pure_greeting_quick(text: str) -> bool:
    """
    Quick check for pure greeting without LLM call.
    Useful for very fast pre-filtering.
    """
    text = text.strip().lower()
    if not text:
        return False
    
    pure_greetings = [
        'اهلا', 'أهلا', 'مرحبا', 'سلام', 'هلا', 'أهلاً', 'مرحباً',
        'hello', 'hi', 'hey', 'greetings', 'howdy', 'sup',
        'صباح الخير', 'مساء الخير', 'good morning', 'good afternoon'
    ]
    
    words = text.split()
    if len(words) > 3:
        return False
    
    return any(greeting in text for greeting in pure_greetings)

def get_cache_stats():
    """Get cache performance statistics"""
    cache_info = check_intent_with_llm.cache_info()
    return {
        'hits': cache_info.hits,
        'misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize
    }

def generate_medical_response(user_input, conversation_context=None):
    """
    Generate response with internal translation for Arabic queries and greeting detection.
    
    Args:
        user_input: The user's message (can include conversation context)
        conversation_context: Optional pre-built conversation context
    
    Returns:
        Dictionary with AI response and analysis
    """
    
    user_language = detect_language(user_input)
    print(f"\n🌐 Detected language: {'العربية' if user_language == 'arabic' else 'English'}")
    
    if is_greeting_or_non_medical(user_input, user_language):
        print("👋 Greeting detected - returning friendly response")
        return {
            'success': True,
            'ai_response': get_greeting_response(user_language),
            'language': user_language,
            'is_greeting': True,
            'search_query_used': None,
            'analysis': {
                'disease': 'N/A',
                'severity': 0,
                'specialty': None,
                'urgency': 'N/A',
                'is_emergency': False
            }
        }
    
    if user_language == 'arabic':
        print("🔄 Internal translation activated for accurate search...")
    
    print("🔍 Analyzing your symptoms...")
    
    analysis = smart_medical_query(user_input, user_language)
    
    if user_language == 'arabic' and analysis.get('search_query_used'):
        print(f"   📝 Search query (translated): '{analysis['search_query_used']}'")
    
    if analysis.get('most_critical'):
        best_match = analysis['most_critical']
        context = best_match.get('text', 'No specific medical information found')
        disease = best_match.get('disease', 'Unknown condition')
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
        context = "No matching disease found in medical database"
        disease = "Not specified" if user_language == 'english' else "غير محدد"
        severity = 0
        specialty = None
        specialty_display = "General Medicine" if user_language == 'english' else "طب عام"
        urgency = get_urgency_arabic(0) if user_language == 'arabic' else get_urgency_english(0)
        emergency_warning = False
    
    if conversation_context:
        prompt = get_response_prompt(
            user_language, context, disease, severity, 
            specialty_display, urgency, emergency_warning, 
            user_input, conversation_context
        )
    else:
        prompt = get_response_prompt(
            user_language, context, disease, severity, 
            specialty_display, urgency, emergency_warning, user_input
        )
    
    print("🤖 Generating response with AI...")
    ai_response = call_openrouter(prompt, user_language)
    
    if ai_response and len(ai_response) > 2:
        if ai_response[0] == '"' and ai_response[-1] == '"':
            ai_response = ai_response[1:-1]
    
    return {
        'success': True,
        'ai_response': ai_response,
        'language': user_language,
        'is_greeting': False,
        'search_query_used': analysis.get('search_query_used'),
        'analysis': {
            'disease': disease,
            'severity': severity,
            'specialty': specialty_display if specialty else None,
            'specialty_raw': specialty,  # Keep original for filtering
            'urgency': urgency,
            'is_emergency': emergency_warning
        }
    }



def generate_dynamic_response_with_llm(conversation_context, user_message, history=None):
    """
    نسخة محسنة جداً لتجنب أخطاء JSON Decode مع Gemini.
    """
    if history is None:
        history = []

    user_language = detect_language(user_message)

    system_prompt = f"""
أنت مساعد ذكي في منصة MediBook لحجز العيادات.

حدد نوع الرسالة بدقة:

- "greeting": تحية فقط.
- "medical": وصف أعراض طبية.
- "doctor_request": طلب عرض دكاترة (كلمات مثل: دكاترة، دكتور، أطباء، اعرضلي، أريني، قولي الدكاترة، عايز دكتور...).

**قواعد مهمة:**
- إذا طلب عرض دكاترة (حتى لو مع أعراض) → اجعل النوع "doctor_request".
- في حالة doctor_request، حدد التخصص المناسب في analysis.specialty (بالإنجليزي: Cardiology, Internal Medicine, Pediatrics...).

**أرجع فقط JSON صالح تماماً بدون أي نص إضافي قبل أو بعد:**

{{
  "type": "doctor_request",
  "ai_response": "الرد الودود للمستخدم",
  "analysis": {{
    "specialty": "Cardiology"
  }}
}}

لا تكتب أي شيء خارج الـ JSON.
"""

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"الرسالة: {user_message}"}
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        }

        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=25
        )

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            raise Exception("API request failed")

        content = response.json()['choices'][0]['message']['content'].strip()

        print(f"Raw AI output: {content[:300]}...")  

        import re
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        json_str = json_str.strip().replace('\n', ' ').replace('```json', '').replace('```', '')

        result = json.loads(json_str)

        result.setdefault('type', 'general')
        result.setdefault('ai_response', "حاضر، ممكن توضح أكثر؟")

        if not isinstance(result.get('analysis'), dict):
            result['analysis'] = {}

        if result.get('type') == 'doctor_request' and not result['analysis'].get('specialty'):
            msg = user_message.lower()
            if 'cardiology' in msg or 'قلب' in msg:
                result['analysis']['specialty'] = 'Cardiology'
            elif 'باطنة' in msg or 'internal' in msg:
                result['analysis']['specialty'] = 'Internal Medicine'
            else:
                result['analysis']['specialty'] = 'Internal Medicine'

        result['success'] = True
        result['language'] = user_language

        print(f"✅ Final Decision: type = {result.get('type')} | Specialty = {result['analysis'].get('specialty')}")

        return result

    except json.JSONDecodeError as je:
        print(f"❌ JSON Decode Error: {je}")
        print(f"Problematic content: {content[:500]}")
    except Exception as e:
        print(f"❌ Error in generate_dynamic_response_with_llm: {str(e)}")

    # Fallback آمن
    return {
        'success': True,
        'type': 'general',
        'ai_response': "حاضر، ممكن توضح طلبك أكثر؟",
        'language': user_language,
        'analysis': {}
    }

import sqlite3
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import json
import os
import requests
import re
from deep_translator import GoogleTranslator

def get_automated_medical_context(patient_id):
    try:
        conn = sqlite3.connect('medibook.db') 
        cursor = conn.cursor()
        

        cursor.execute('''
            SELECT specialty 
            FROM appointments 
            WHERE patient_id = ? 
            ORDER BY appointment_date DESC LIMIT 1
        ''', (patient_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0] 
        return "General"
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return "General"


def get_followup_prompt(history, current_symptoms, language='arabic'):
    """Enhanced prompt that knows the previous specialty"""
    
    specialty = history.get('last_specialty', 'General Medicine')
    
    if language == 'arabic':
        return f"""أنت مساعد طبي شخصي لمتابعة حالة المريض.

**المعلومات السابقة (من آخر حجز):**
- التخصص السابق: {specialty}
- التشخيص السابق: {history['diagnosis']}
- شدة الأعراض السابقة: {history['severity']}/10
- الأعراض السابقة: {history['symptoms']}
- الأدوية: {history['meds'] or 'لا يوجد'}

**الأعراض الحالية التي يصفها المريض:** "{current_symptoms}"

**المطلوب منك:**
1. قارن الأعراض الحالية بالأعراض السابقة في التخصص {specialty}
2. حدد بوضوح: (تحسنت / مستقرة / تدهورت)
3. إذا تدهورت → اذكر العلامات الخطيرة
4. أعطِ نصيحة واضحة: هل يحتاج تغيير علاج أو مراجعة عاجلة؟
5. أضف التنويه: "تنبيه: هذه متابعة أولية ولا تغني عن استشارة الطبيب."

**الرد:**"""
    
    else:
        return f"""You are a personalized medical follow-up assistant.

**Previous Record (Last Appointment):**
- Previous Specialty: {specialty}
- Previous Diagnosis: {history['diagnosis']}
- Previous Severity: {history['severity']}/10
- Previous Symptoms: {history['symptoms']}
- Medications: {history['meds'] or 'None'}

**Current Symptoms:** "{current_symptoms}"

**Instructions:**
1. Compare current symptoms with the previous ones in {specialty}
2. Clearly state: (Improved / Stable / Worsened)
3. If worsened → mention any red flags
4. Give clear advice: medication change or urgent visit?
5. Add disclaimer: "Disclaimer: This is preliminary follow-up only."

**Response:**"""



def get_patient_history(patient_id):
    """جلب آخر سجل متابعة أو آخر حجز"""
    if not patient_id:
        return None

    patient_id = str(patient_id).strip()

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    last_diagnosis,
                    last_severity,
                    medications,
                    last_symptoms,
                    timestamp,
                    'FollowUp' as source
                FROM FollowUp_History 
                WHERE patient_id = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (patient_id,))
            
            row = cursor.fetchone()

            if row:
                history = dict(row)
                print(f"✅ Found FollowUp history for patient {patient_id}")
                return history

            cursor.execute('''
                SELECT 
                    u.specialty as last_specialty,
                    a.date as last_appointment_date,
                    'Appointment' as source
                FROM appointments a
                JOIN users u ON a.doctor_id = u._id
                WHERE a.patient_id = ?
                ORDER BY a._id DESC LIMIT 1
            ''', (patient_id,))
            
            row = cursor.fetchone()
            if row:
                history = dict(row)
                history['last_diagnosis'] = history.get('last_specialty', 'غير محدد')
                history['last_severity'] = 5
                history['last_symptoms'] = 'لا توجد أعراض سابقة'
                print(f"✅ Found Appointment history for patient {patient_id} → {history.get('last_specialty')}")
                return history

            print(f"ℹ️ No history at all for patient {patient_id}")
            return None

    except Exception as e:
        print(f"⚠️ Error in get_patient_history: {e}")
        return None

def save_session_to_db(patient_id, diagnosis, severity, meds, symptoms):
    """حفظ جلسة المتابعة في نفس قاعدة medibook.db"""
    try:
        with get_db() as conn:   
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO FollowUp_History 
                (patient_id, last_diagnosis, last_severity, medications, last_symptoms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(patient_id),
                diagnosis or "غير محدد",
                int(severity) if severity is not None else 5,
                meds or "",
                symptoms.strip(),
                now
            ))

            conn.commit()   

        print(f"✅ SAVED SUCCESSFULLY → Patient {patient_id} | Diagnosis: {diagnosis} | Symptoms: {symptoms[:70]}...")

    except Exception as e:
        print(f"❌ ERROR in save_session_to_db: {e}")
        import traceback
        traceback.print_exc()






def generate_vip_personalized_response(patient_id: str, user_input: str):
    """VIP Follow-up ذكي + حفظ + مقارنة مع الأعراض السابقة (نسخة محسنة)"""
    
    if not patient_id or str(patient_id).strip() == "":
        return {
            'success': False, 
            'ai_response': 'عذراً، هذه الخدمة للمرضى المسجلين فقط.',
            'language': detect_language(user_input)
        }

    history = get_patient_history(patient_id)
    user_language = detect_language(user_input)

    if not history:
        return {
            'success': True,
            'ai_response': "مرحباً! 👋 لسه مفيش سجل سابق ليك. لو عندك أي أعراض أو استفسار، وصفها لي وأنا هتابع معاك.",
            'language': user_language,
            'is_vip': True,
            'analysis': {'is_followup': False}
        }

    prev_symptoms = history.get('last_symptoms', 'لا توجد أعراض سابقة')
    specialty = history.get('last_specialty', 'طب عام')
    prev_severity = int(history.get('last_severity', 5))
    
    final_diagnosis = history.get('last_diagnosis') or specialty or "متابعة أطفال"

    prompt = f"""أنت مدرب طبي شخصي ذكي متخصص في متابعة الأطفال في تخصص {specialty}.

**السجل السابق:**
- الأعراض السابقة: {prev_symptoms}
- شدة الأعراض السابقة: {prev_severity}/10
- التشخيص/التخصص: {final_diagnosis}

**كلام المريض دلوقتي:** "{user_input}"

**مهمتك:**
1. قارن الحالة الحالية بالسابقة بوضوح جدًا (تحسنت / مستقرة / تدهورت).
2. ركز على الأعراض اللي كانت موجودة قبل كده (مثل الكحة أو الحرارة أو الأكل).
3. لو تحسن → أبرز التحسن وشجع الأهل.
4. لو لسه فيه أعراض → اقترح نصيحة بسيطة ومنطقية.
5. لو تدهور → أعطِ تحذير واضح ونصيحة عاجلة.

رد بلهجة مصرية ودودة، مطمئنة، وسهلة. 
أنهي الرد دايماً بـ:
"تنبيه: هذه متابعة أولية فقط ولا تغني عن زيارة الطبيب المختص."""

    ai_response = call_openrouter(prompt, user_language)

    try:
        save_session_to_db(
            patient_id=str(patient_id),
            diagnosis=final_diagnosis,     
            severity=prev_severity,
            meds=history.get('medications', ""),
            symptoms=user_input
        )
        print(f"✅ SAVED SUCCESSFULLY → Patient {patient_id} | Diagnosis: {final_diagnosis} | Symptoms: {user_input[:60]}...")
    except Exception as e:
        print(f"⚠️ فشل حفظ الجلسة: {e}")
        import traceback
        traceback.print_exc()

    return {
        'success': True,
        'ai_response': ai_response,
        'language': user_language,
        'is_vip': True,
        'patient_id': patient_id,
        'analysis': {
            'previous_specialty': specialty,
            'previous_symptoms': prev_symptoms,
            'previous_severity': prev_severity,
            'current_diagnosis': final_diagnosis,
            'is_followup': True
        }
    }

def main():
    print("="*60)
    print("🏥 AI Medical Assistant - Clinic Booking System")
    print("🌐 Multi-Language Support (Arabic / English)")
    print("🔄 Internal Translation: Arabic → English for accurate search")
    print("👋 Smart Greeting Detection: No more false matches!")
    print("💬 You can type in Arabic or English - I'll respond in the same language!")
    print("="*60)
    
    print("\n📝 Example queries you can try:")
    print("   • English: 'I have a severe headache'")
    print("   • Arabic: 'عندي صداع شديد'")
    print("   • Arabic: 'عندي طفح جلدي وحكة'")
    print("   • English: 'chest pain and difficulty breathing'")
    print("   • Try: 'اهلا' or 'hello' - See the greeting response!")
    
    while True:
        print("\n" + "-"*60)
        user_input = input("💬 Enter your symptoms / أدخل الأعراض (or 'quit' للخروج): ")
        
        if user_input.lower() in ['quit', 'exit', 'q', 'خروج']:
            print("\n👋 Thank you! / شكراً لك! Wishing you good health / مع أمنياتنا بدوام الصحة!")
            break
        
        if not user_input.strip():
            print("❌ Please enter symptoms / الرجاء إدخال الأعراض")
            continue
        
        intent = check_intent_with_llm(user_input)
        
        if intent == "greeting":
            print("\n🤖 **Response / الرد:**")
            print("-"*60)
            if any(arabic_char in user_input for arabic_char in ['ا', 'ب', 'ت', 'ث', 'ج']):
                print("🏥 أهلاً وسهلاً بك! 👋\nكيف يمكنني مساعدتك اليوم؟ من فضلك صف لي أعراضك الطبية لأتمكن من مساعدتك في اختيار العيادة المناسبة.\n🩺")
            else:
                print("🏥 Welcome! 👋\nHow can I help you today? Please describe your medical symptoms so I can help you find the right clinic.\n🩺")
            print("-"*60)
            continue  
        
        result = generate_medical_response(user_input)
        
        if result['success']:
            if result['analysis']['is_emergency']:
                print("\n" + "="*60)
                if result['language'] == 'arabic':
                    print("🚨 🚨 🚨 تَنْبِيه طارئ 🚨 🚨 🚨")
                else:
                    print("🚨 🚨 🚨 EMERGENCY ALERT 🚨 🚨 🚨")
                print("="*60)
                print(result['analysis']['urgency'])
                print("="*60)
            
            print("\n🤖 **Response / الرد:**")
            print("-"*60)
            print(result['ai_response'])
            print("-"*60)
            
            if not result.get('is_greeting', False):
                print(f"\n📋 Information / معلومات:")
                if result['language'] == 'arabic':
                    print(f"   • المرض المحتمل: {result['analysis']['disease']}")
                    print(f"   • درجة الخطورة: {result['analysis']['severity']}/10")
                    print(f"   • التخصص المقترح: {result['analysis']['specialty']}")
                    print(f"   • {result['analysis']['urgency']}")
                    print(f"   • 🔍 تم البحث باستخدام: '{result['search_query_used']}'")
                else:
                    print(f"   • Potential Condition: {result['analysis']['disease']}")
                    print(f"   • Severity Level: {result['analysis']['severity']}/10")
                    print(f"   • Recommended Specialty: {result['analysis']['specialty']}")
                    print(f"   • {result['analysis']['urgency']}")
                    if result['search_query_used']:
                        print(f"   • 🔍 Searched using: '{result['search_query_used']}'")
        
        else:
            print(f"\n❌ Error / خطأ: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()




__all__ = [
    'check_intent_with_llm',
    'generate_medical_response',
    'generate_dynamic_response_with_llm',   
    'detect_language',
    'is_greeting_or_non_medical',
    'get_greeting_response',
    'smart_medical_query',
    'get_specialty_arabic',
    'get_urgency_arabic',
    'get_urgency_english',
    'call_openrouter',
    'get_response_prompt',
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
    get_patient_history,
    map_to_app_specialty,
    build_conversation_context,
    get_response_prompt_with_context,
    generate_medical_response_with_context,
    get_automated_medical_context
]