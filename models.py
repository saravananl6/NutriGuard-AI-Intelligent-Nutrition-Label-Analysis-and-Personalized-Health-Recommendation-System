from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_local_time():
    """Get current local time"""
    return datetime.now()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_local_time)
    
    # Relationship with nutrition checks
    checks = db.relationship('NutritionCheck', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class NutritionCheck(db.Model):
    __tablename__ = 'nutrition_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Weight in kg
    image_path = db.Column(db.String(255), nullable=False)
    ocr_text = db.Column(db.Text)
    decision = db.Column(db.String(50), nullable=False)  # Recommended or Not Recommended
    safe_factors = db.Column(db.Text)  # JSON string
    risk_factors = db.Column(db.Text)  # JSON string
    reason = db.Column(db.Text)
    daily_guidelines = db.Column(db.Text)  # JSON string - recommended daily intake
    checked_at = db.Column(db.DateTime, default=get_local_time)
    email_sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<NutritionCheck {self.id} - {self.decision}>'