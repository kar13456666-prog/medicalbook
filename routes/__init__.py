from flask import Blueprint

# تعريف الـ Blueprints
auth_bp = Blueprint('auth', __name__)
doctors_bp = Blueprint('doctors', __name__)
clinics_bp = Blueprint('clinics', __name__)
appointments_bp = Blueprint('appointments', __name__)
reviews_bp = Blueprint('reviews', __name__)
ai_bp = Blueprint('ai', __name__)
analytics_bp = Blueprint('analytics', __name__)
slots_bp = Blueprint('slots', __name__)

# استيراد الـ routes (بعد تعريف الـ Blueprints لتجنب الـ circular import)
from . import auth, doctors, clinics, appointments, reviews, ai_chat, analytics, slots