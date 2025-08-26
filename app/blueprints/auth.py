from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        user = User.get_by_username(username) or User.get_by_email(username)
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('main.dashboard')})
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            error_msg = 'Invalid username/email or password'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 401
            
            flash(error_msg, 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            signup_code = data.get('signup_code')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            signup_code = request.form.get('signup_code')
        
        errors = []
        
        # Validation
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Validate sign-up code
        required_signup_code = current_app.config.get('SIGNUP_CODE', 'VOICE2024')
        if not signup_code or signup_code != required_signup_code:
            errors.append('Invalid sign-up code')
        
        # Check if user already exists
        current_app.logger.info(f"Checking if username exists: {username}")
        if User.get_by_username(username):
            current_app.logger.info(f"Username already exists: {username}")
            errors.append('Username already exists')
        
        current_app.logger.info(f"Checking if email exists: {email}")
        if User.get_by_email(email):
            current_app.logger.info(f"Email already exists: {email}")
            errors.append('Email already registered')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            
            for error in errors:
                flash(error, 'error')
        else:
            # Create user
            user = User.create(username, email, password)
            login_user(user, remember=True)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('main.dashboard')})
            
            flash('Account created successfully! Welcome to Voice Log.', 'success')
            return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    errors = []
    
    if not current_user.check_password(current_password):
        errors.append('Current password is incorrect')
    
    if not new_password or len(new_password) < 6:
        errors.append('New password must be at least 6 characters long')
    
    if new_password != confirm_password:
        errors.append('New passwords do not match')
    
    if errors:
        for error in errors:
            flash(error, 'error')
    else:
        current_user.update_password(new_password)
        flash('Password updated successfully!', 'success')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/update_ai_training', methods=['POST'])
@login_required
def update_ai_training():
    """Update AI training data for the current user"""
    ai_bio = request.form.get('ai_bio', '').strip()
    ai_writing_samples = request.form.get('ai_writing_samples', '').strip()
    
    try:
        current_user.update_ai_training(ai_bio, ai_writing_samples)
        flash('AI training data updated successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating AI training data: {e}")
        flash('Error updating AI training data. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    display_name = request.form.get('display_name', '').strip()
    website = request.form.get('website', '').strip()
    short_bio = request.form.get('short_bio', '').strip()
    instagram = request.form.get('instagram', '').strip()
    linkedin = request.form.get('linkedin', '').strip()
    twitter = request.form.get('twitter', '').strip()
    facebook = request.form.get('facebook', '').strip()
    
    try:
        current_user.update_profile(
            display_name=display_name if display_name else None,
            website=website if website else None,
            short_bio=short_bio if short_bio else None,
            instagram=instagram if instagram else None,
            linkedin=linkedin if linkedin else None,
            twitter=twitter if twitter else None,
            facebook=facebook if facebook else None
        )
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        flash('Error updating profile. Please try again.', 'error')
    
    return redirect(url_for('auth.profile'))