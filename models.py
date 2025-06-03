import uuid
from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship with worksheets
    worksheets = db.relationship('Worksheet', backref='user', lazy=True)

class Worksheet(db.Model):
    __tablename__ = "worksheets"
    
    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    prompt_json = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|in_progress|done|error
    pdf_path = db.Column(db.String(255), nullable=True)
    interactive_path = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    # Store embedding as array of floats - pgvector integration would require additional setup
    embedding = db.Column(ARRAY(db.Float), nullable=True)
