import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, NutritionCheck
from utils import extract_text_from_image, analyze_nutrition_with_groq, allowed_file
from email_service import mail, send_alert_email

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Route to serve uploaded files
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        
        # Create new user
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/home')
@login_required
def home():
    """User home dashboard"""
    # Get recent checks
    recent_checks = NutritionCheck.query.filter_by(user_id=current_user.id)\
        .order_by(NutritionCheck.checked_at.desc()).limit(5).all()
    
    # Statistics
    total_checks = NutritionCheck.query.filter_by(user_id=current_user.id).count()
    recommended_count = NutritionCheck.query.filter_by(user_id=current_user.id, decision='Recommended').count()
    not_recommended_count = NutritionCheck.query.filter_by(user_id=current_user.id, decision='Not Recommended').count()
    
    return render_template('home.html', 
                         recent_checks=recent_checks,
                         total_checks=total_checks,
                         recommended_count=recommended_count,
                         not_recommended_count=not_recommended_count)


@app.route('/checker', methods=['GET', 'POST'])
@login_required
def checker():
    """Nutrition label checker"""
    if request.method == 'POST':
        age = request.form.get('age')
        weight = request.form.get('weight')
        
        # Validate age
        try:
            age = int(age)
            if age < 1 or age > 120:
                flash('Please enter a valid age between 1 and 120.', 'danger')
                return redirect(url_for('checker'))
        except (ValueError, TypeError):
            flash('Please enter a valid age.', 'danger')
            return redirect(url_for('checker'))
        
        # Validate weight
        try:
            weight = float(weight)
            if weight < 2 or weight > 500:
                flash('Please enter a valid weight between 2 and 500 kg.', 'danger')
                return redirect(url_for('checker'))
        except (ValueError, TypeError):
            flash('Please enter a valid weight.', 'danger')
            return redirect(url_for('checker'))
        
        # Check if file was uploaded
        if 'nutrition_label' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(url_for('checker'))
        
        file = request.files['nutrition_label']
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('checker'))
        
        if file and allowed_file(file.filename):
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text using OCR
            ocr_text = extract_text_from_image(filepath)
            
            if not ocr_text:
                flash('Could not extract text from image. Please ensure the image is clear.', 'warning')
                os.remove(filepath)
                return redirect(url_for('checker'))
            
            # Analyze with Groq (now includes weight)
            analysis = analyze_nutrition_with_groq(ocr_text, age, weight)
            
            # Extract daily guidelines
            daily_guidelines = analysis.get('daily_guidelines', {})
            
            # Save to database
            check = NutritionCheck(
                user_id=current_user.id,
                age=age,
                weight=weight,
                image_path=filepath,
                ocr_text=ocr_text,
                decision=analysis['decision'],
                safe_factors=json.dumps(analysis['safe_factors']),
                risk_factors=json.dumps(analysis['risk_factors']),
                reason=analysis['reason'],
                daily_guidelines=json.dumps(daily_guidelines)
            )
            db.session.add(check)
            db.session.commit()
            
            # Send email if not recommended
            if analysis['decision'] == 'Not Recommended':
                email_sent = send_alert_email(current_user.email, check)
                check.email_sent = email_sent
                db.session.commit()
            
            flash('Analysis complete!', 'success')
            return redirect(url_for('result', check_id=check.id))
        else:
            flash('Invalid file type. Please upload an image file.', 'danger')
            return redirect(url_for('checker'))
    
    return render_template('checker.html')


@app.route('/result/<int:check_id>')
@login_required
def result(check_id):
    """Display analysis result"""
    check = NutritionCheck.query.get_or_404(check_id)
    
    # Ensure user owns this check
    if check.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    # Parse JSON fields
    safe_factors = json.loads(check.safe_factors) if check.safe_factors else []
    risk_factors = json.loads(check.risk_factors) if check.risk_factors else []
    daily_guidelines = json.loads(check.daily_guidelines) if check.daily_guidelines else {}
    
    return render_template('result.html', 
                         check=check,
                         safe_factors=safe_factors,
                         risk_factors=risk_factors,
                         daily_guidelines=daily_guidelines)


@app.route('/history')
@login_required
def history():
    """View all nutrition checks history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    checks = NutritionCheck.query.filter_by(user_id=current_user.id)\
        .order_by(NutritionCheck.checked_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('history.html', checks=checks)


@app.route('/history/<int:check_id>')
@login_required
def history_detail(check_id):
    """View detailed history of a specific check"""
    check = NutritionCheck.query.get_or_404(check_id)
    
    # Ensure user owns this check
    if check.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('history'))
    
    # Parse JSON fields
    safe_factors = json.loads(check.safe_factors) if check.safe_factors else []
    risk_factors = json.loads(check.risk_factors) if check.risk_factors else []
    daily_guidelines = json.loads(check.daily_guidelines) if check.daily_guidelines else {}
    
    return render_template('history_detail.html', 
                         check=check,
                         safe_factors=safe_factors,
                         risk_factors=risk_factors,
                         daily_guidelines=daily_guidelines)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)