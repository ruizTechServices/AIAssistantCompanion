import os
import logging
from flask import Flask, send_from_directory, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = "google_auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    logging.info(f"Loading user with ID: {user_id}")
    try:
        user = User.query.get(int(user_id))
        logging.info(f"Loaded user: {user.email if user else 'None'}")
        return user
    except Exception as e:
        logging.error(f"Error loading user {user_id}: {e}")
        return None

# Register blueprints
from google_auth import google_auth
app.register_blueprint(google_auth)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

@app.route("/")
def index():
    logging.info(f"Index route accessed. Current user authenticated: {current_user.is_authenticated}")
    logging.info(f"Current user: {current_user}")
    logging.info(f"Session data: {session}")
    
    if not current_user.is_authenticated:
        logging.info("User not authenticated, showing login page")
        return send_from_directory("static", "login.html")
    
    logging.info(f"User authenticated: {current_user.email}, showing main app")
    return send_from_directory("static", "index.html")

@app.route("/api/worksheet", methods=["POST"])
@login_required
def create_worksheet():
    """Create a new worksheet generation job."""
    from worker import start_generation_job
    from models import Worksheet
    import uuid
    import json
    
    data = request.get_json()
    required_fields = {"gradeLevel", "topic", "activities", "style", "imagesAllowed"}
    
    if not data or not required_fields.issubset(data.keys()):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate embedding for the topic
    from llm_client import generate_embedding
    try:
        logging.info(f"Generating embedding for topic: {data['topic']}")
        embedding = generate_embedding(data["topic"])
        logging.info(f"Embedding generated successfully with {len(embedding)} dimensions")
    except Exception as e:
        logging.error(f"Failed to generate embedding: {e}")
        return jsonify({"error": "Failed to process request"}), 500
    
    # Create new worksheet record
    job_id = str(uuid.uuid4())
    logging.info(f"Creating worksheet record with job_id: {job_id}")
    
    worksheet = Worksheet(
        id=job_id,
        user_id=current_user.id,
        prompt_json=data,
        embedding=embedding,
        status="pending"
    )
    
    try:
        db.session.add(worksheet)
        db.session.commit()
        logging.info(f"Worksheet record saved to database: {job_id}")
    except Exception as e:
        logging.error(f"Database error saving worksheet: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500
    
    # Start background job
    logging.info(f"Starting background job for worksheet: {job_id}")
    try:
        start_generation_job(job_id)
        logging.info(f"Background job started successfully for: {job_id}")
    except Exception as e:
        logging.error(f"Failed to start background job: {e}")
        return jsonify({"error": "Failed to start generation"}), 500
    
    return jsonify({"job_id": job_id}), 202

@app.route("/api/worksheet/<job_id>/status")
@login_required
def get_worksheet_status(job_id):
    """Get the status of a worksheet generation job."""
    from models import Worksheet
    
    worksheet = Worksheet.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not worksheet:
        return jsonify({"error": "Worksheet not found"}), 404
    
    response = {
        "status": worksheet.status,
        "progress_step": worksheet.progress_step,
        "progress_percent": worksheet.progress_percent,
        "created_at": worksheet.created_at.isoformat()
    }
    
    if worksheet.status == "done":
        response["pdf_path"] = worksheet.pdf_path
        response["interactive_path"] = worksheet.interactive_path
    elif worksheet.status == "error":
        response["error_message"] = worksheet.error_message
    
    return jsonify(response)

@app.route("/api/worksheet/<job_id>/cancel", methods=['POST'])
@login_required
def cancel_worksheet(job_id):
    """Cancel a worksheet generation job."""
    from models import Worksheet
    
    worksheet = Worksheet.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not worksheet:
        return jsonify({"error": "Worksheet not found"}), 404
    
    # Only allow cancelling if job is pending or in progress
    if worksheet.status in ['pending', 'in_progress']:
        worksheet.status = 'cancelled'
        worksheet.progress_step = 'Cancelled by user'
        db.session.commit()
        logging.info(f"Worksheet {job_id} cancelled by user {current_user.id}")
        return jsonify({'success': True, 'message': 'Worksheet generation cancelled'})
    else:
        return jsonify({'success': False, 'message': 'Cannot cancel completed or error jobs'}), 400

@app.route("/worksheets/<path:filename>")
@login_required
def serve_worksheet(filename):
    """Serve generated worksheet files."""
    return send_from_directory("worksheets", filename)

@app.route("/api/worksheets")
@login_required
def list_worksheets():
    """List all worksheets for the current user."""
    from models import Worksheet
    
    worksheets = Worksheet.query.filter_by(user_id=current_user.id).order_by(Worksheet.created_at.desc()).all()
    
    result = []
    for ws in worksheets:
        result.append({
            "id": ws.id,
            "created_at": ws.created_at.isoformat(),
            "status": ws.status,
            "topic": ws.prompt_json.get("topic", ""),
            "grade_level": ws.prompt_json.get("gradeLevel", ""),
            "pdf_path": ws.pdf_path,
            "interactive_path": ws.interactive_path
        })
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
