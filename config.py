# config.py
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# --- OpenRouter Configuration ---
# بنقرأ المفتاح من الـ Environment Variable، ولو مش موجود بنستخدم placeholder فارغ
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# --- Database Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "medibook.db")

# --- ChromaDB Path Configuration ---
# لو إحنا جوه Docker بنستخدم المسار الداخلي، لو بره بنستخدم المسار اللي في الـ .env أو المسار القديم
if os.path.exists("/.dockerenv"):
    CHROMA_PATH = "/app/chroma_data"
else:
    # بيقرأ CHROMA_PATH من .env، ولو مش موجود بيستخدم المسار القديم بتاعك كـ Default
    CHROMA_PATH = os.getenv("CHROMA_PATH", r'D:\cli\data')

# طباعة للتأكد من المسارات عند التشغيل (اختياري)
print(f"--- Configuration Loaded ---")
print(f"Database Path: {DATABASE_PATH}")
print(f"ChromaDB Path: {CHROMA_PATH}")