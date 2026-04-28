import os
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "medibook.db")


if os.path.exists("/.dockerenv"):
    CHROMA_PATH = "/app/chroma_data"
else:
    CHROMA_PATH = os.getenv("CHROMA_PATH", r'D:\cli\data')

print(f"--- Configuration Loaded ---")
print(f"Database Path: {DATABASE_PATH}")
print(f"ChromaDB Path: {CHROMA_PATH}")