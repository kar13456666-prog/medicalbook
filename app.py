from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_database
import traceback
import logging

# استيراد الـ Blueprints
from routes import (
    auth_bp, doctors_bp, clinics_bp, appointments_bp,
    reviews_bp, ai_bp, analytics_bp, slots_bp
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== CORS Configuration ==========
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        "expose_headers": ["Content-Disposition"],
        "supports_credentials": True,
        "max_age": 86400,
    },
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "supports_credentials": True,
    }
})

# ========== CORS Middleware ==========
@app.before_request
def handle_options_request():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = app.make_response("")
        origin = request.headers.get("Origin", "")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        response.headers["Access-Control-Max-Age"] = "86400"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 204

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response"""
    origin = request.headers.get("Origin")
    allowed_origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200"]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

# ========== Global Error Handlers ==========

@app.errorhandler(400)
def bad_request_error(e):
    """Handle 400 Bad Request errors"""
    logger.error(f"Bad Request: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": "The request was invalid. Please check your input."
    }), 400

@app.errorhandler(401)
def unauthorized_error(e):
    """Handle 401 Unauthorized errors"""
    logger.error(f"Unauthorized: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": "Please login to access this resource."
    }), 401

@app.errorhandler(403)
def forbidden_error(e):
    """Handle 403 Forbidden errors"""
    logger.error(f"Forbidden: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Forbidden",
        "message": "You don't have permission to access this resource."
    }), 403

@app.errorhandler(404)
def not_found_error(e):
    """Handle 404 Not Found errors"""
    logger.error(f"Not Found: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Not found",
        "message": "The requested resource was not found."
    }), 404

@app.errorhandler(405)
def method_not_allowed_error(e):
    """Handle 405 Method Not Allowed errors"""
    logger.error(f"Method Not Allowed: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": f"The {request.method} method is not allowed for this endpoint."
    }), 405

@app.errorhandler(409)
def conflict_error(e):
    """Handle 409 Conflict errors"""
    logger.error(f"Conflict: {str(e)}")
    return jsonify({
        "success": False,
        "error": "Conflict",
        "message": "The resource already exists or there is a conflict."
    }), 409

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 Internal Server errors"""
    logger.error(f"Internal Server Error: {str(e)}")
    traceback.print_exc()
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

# ========== Global Exception Handler ==========
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled Exception: {str(e)}")
    traceback.print_exc()
    
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

# ========== Request Logging Middleware ==========
@app.before_request
def log_request_info():
    """Log incoming request details for debugging"""
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        logger.info(f"📨 {request.method} {request.path} - Data: {request.get_json(silent=True)}")
    else:
        logger.info(f"📨 {request.method} {request.path} - Args: {dict(request.args)}")

@app.after_request
def log_response_info(response):
    """Log response status for debugging"""
    logger.info(f"📤 {request.method} {request.path} - Status: {response.status_code}")
    return response

# ========== Register Blueprints ==========
app.register_blueprint(auth_bp)
app.register_blueprint(doctors_bp)
app.register_blueprint(clinics_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(slots_bp)

logger.info("✅ All blueprints registered successfully")

# ========== Health Check Endpoints ==========
@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Medical Assistant API",
        "version": "1.0.0",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with database status"""
    try:
        from database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()["count"]
        
        return jsonify({
            "status": "healthy",
            "service": "Medical Assistant API",
            "version": "1.0.0",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "database": {
                "connected": True,
                "user_count": user_count
            },
            "blueprints": [
                "auth", "doctors", "clinics", "appointments",
                "reviews", "ai", "analytics", "slots"
            ]
        }), 200
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({
            "status": "degraded",
            "error": str(e),
            "database": {"connected": False}
        }), 500

# ========== API Info Endpoint ==========
@app.route('/api/info', methods=['GET'])
def api_info():
    """Get API information and available endpoints"""
    endpoints = {
        "auth": [
            "POST /api/signup",
            "POST /api/login"
        ],
        "doctors": [
            "GET /api/manager/doctors",
            "POST /api/manager/add-doctor",
            "GET /api/manager/doctor/<id>",
            "PUT /api/manager/doctor/<id>",
            "DELETE /api/manager/doctor/<id>",
            "GET /api/doctor/<id>/clinics",
            "GET /api/doctor/<id>/quick-stats"
        ],
        "clinics": [
            "GET /api/manager/clinics",
            "POST /api/manager/add-clinic",
            "PUT /api/manager/clinic/<id>",
            "DELETE /api/manager/clinic/<id>",
            "GET /api/clinics/<id>"
        ],
        "appointments": [
            "POST /api/appointments/book",
            "GET /api/patient/<id>/appointments",
            "PATCH /api/appointments/<id>/status",
            "POST /api/appointments/<id>/cancel"
        ],
        "reviews": [
            "GET /api/doctor/<id>/reviews",
            "POST /api/appointments/<id>/review",
            "PUT /api/reviews/<id>",
            "DELETE /api/reviews/<id>"
        ],
        "ai_chat": [
            "POST /chat",
            "POST /chat/specialty-only",
            "POST /api/vip-chat/<patient_id>/message",
            "GET /api/patient/<patient_id>/vip-health-summary"
        ],
        "analytics": [
            "GET /api/doctor/<id>/analytics",
            "GET /api/doctor/<id>/appointments/count",
            "GET /api/doctor/<id>/appointments/stats",
            "GET /api/manager/analytics"
        ],
        "slots": [
            "GET /api/doctor/<id>/available-slots",
            "POST /api/doctor/<id>/manual-slot",
            "PUT /api/doctor/<id>/available-slots/<slot_id>",
            "DELETE /api/doctor/<id>/available-slots/<slot_id>",
            "POST /api/doctor/<id>/generate-slots-range"
        ]
    }
    
    return jsonify({
        "success": True,
        "service": "Medical Assistant API",
        "version": "1.0.0",
        "endpoints": endpoints
    }), 200

# ========== Initialize Database ==========
try:
    init_database()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {str(e)}")
    traceback.print_exc()

# ========== Run App ==========
if __name__ == '__main__':
    logger.info("🚀 Starting Medical Assistant API Server...")
    logger.info("📍 Running on: http://localhost:5000")
    logger.info("📋 API Info: http://localhost:5000/api/info")
    logger.info("💚 Health Check: http://localhost:5000/health")
    
    app.run(
        debug=True, 
        port=5000, 
        threaded=True,
        host='0.0.0.0'  # Allow external connections
    )