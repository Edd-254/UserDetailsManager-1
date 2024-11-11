import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, make_response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import text, func
from functools import wraps
import pdfkit

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app first
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_only_for_development")

# Get database URL and verify format
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    logger.critical("DATABASE_URL environment variable is not set")
    raise ValueError("DATABASE_URL must be set")

logger.info(f"Database URL format: {db_url.split(':')[0]}")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "echo": True  # Enable SQL statement logging
}

# Initialize SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import models after db initialization
from models import User

# Import forms after app initialization
from forms import RegistrationForm, EditProfileForm, LoginForm

def create_admin_user():
    try:
        logger.debug("Starting admin user creation process")
        
        # Check if admin exists
        admin = User.query.filter_by(user_id='admin').first()
        if admin:
            logger.info("Admin user already exists")
            return True
            
        # Create new admin user
        admin = User()
        admin.user_id = 'admin'
        admin.password_hash = generate_password_hash('adminpass123')
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        admin.address = 'System Address'
        admin.gender = 'other'
        admin.phone = '(000) 000-0000'
        admin.email = 'admin@system.local'
        admin.is_admin = True
        
        logger.debug("Adding admin user to session")
        db.session.add(admin)
        
        logger.debug("Committing admin user to database")
        db.session.commit()
        
        # Verify admin was created
        created_admin = User.query.filter_by(user_id='admin').first()
        if not created_admin or not created_admin.is_admin:
            logger.error("Admin user verification failed")
            return False
            
        logger.info("Admin user created and verified successfully")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        return False

def init_db():
    """Initialize database and create admin user."""
    try:
        logger.info("Starting database initialization...")
        with app.app_context():
            try:
                logger.debug("Testing database connection...")
                db.session.execute(text('SELECT version()'))
                logger.info("Database connection test successful")
            except OperationalError as e:
                logger.error(f"Database connection failed: {str(e)}")
                return False
            except SQLAlchemyError as e:
                logger.error(f"Database query failed: {str(e)}")
                return False
            
            try:
                inspector = db.inspect(db.engine)
                existing_tables = inspector.get_table_names()
                logger.debug(f"Existing tables: {existing_tables}")
                
                db.create_all()
                logger.info("Database tables created successfully")
                
                new_tables = db.inspect(db.engine).get_table_names()
                logger.debug(f"Tables after creation: {new_tables}")
                
                # Create admin user after tables are created
                logger.info("Attempting to create admin user...")
                if create_admin_user():
                    logger.info("Admin user setup completed successfully")
                else:
                    logger.error("Failed to setup admin user")
                    return False
                
                return True
            except SQLAlchemyError as e:
                logger.error(f"Failed to create database tables: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Database initialization failed with unexpected error: {str(e)}")
        return False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('users'))
        
    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Login attempt for user_id: {form.user_id.data}")
        user = User.query.filter_by(user_id=form.user_id.data).first()
        
        if not user:
            logger.warning(f"No user found with user_id: {form.user_id.data}")
            flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form)
            
        if check_password_hash(user.password_hash, form.password.data):
            logger.info(f"Successful login for user: {user.user_id}")
            session['user_id'] = user.user_id
            session['user_name'] = user.get_full_name()
            session['is_admin'] = user.is_admin
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard') if user.is_admin else url_for('users'))
            
        logger.warning(f"Invalid password for user: {user.user_id}")
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('users'))
        
    form = RegistrationForm()
    if request.method == 'POST':
        logger.info("Processing registration request")
        logger.debug(f"Form data: {form.data}")
        
        if form.validate():
            try:
                existing_user = User.query.filter(
                    (User.user_id == form.user_id.data) | 
                    (User.email == form.email.data)
                ).first()
                
                if existing_user:
                    if existing_user.user_id == form.user_id.data:
                        flash('User ID already taken. Please choose another.', 'danger')
                    else:
                        flash('Email already registered. Please use another email.', 'danger')
                    return render_template('register.html', form=form)

                user = User()
                user.user_id = form.user_id.data
                user.password_hash = generate_password_hash(form.password.data)
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.address = form.address.data
                user.gender = form.gender.data
                user.phone = form.phone.data
                user.email = form.email.data
                
                logger.debug(f"Creating new user: {user}")
                db.session.add(user)
                db.session.commit()
                logger.info(f"New user registered successfully: {user}")
                
                session['user_id'] = user.user_id
                session['user_name'] = user.get_full_name()
                session['is_admin'] = user.is_admin
                
                flash('Registration successful!', 'success')
                return redirect(url_for('users'))

            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Database integrity error during registration: {str(e)}")
                flash('Registration failed due to data conflict. Please try again.', 'danger')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Unexpected error during registration: {str(e)}")
                flash('An unexpected error occurred. Please try again.', 'danger')
        else:
            logger.warning(f"Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/users')
@login_required
def users():
    try:
        users = User.query.all()
        return render_template('users.html', users=users)
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching users: {str(e)}")
        flash('Error loading users. Please try again.', 'danger')
        return redirect(url_for('register'))
    except Exception as e:
        logger.error(f"Unexpected error while fetching users: {str(e)}")
        flash('An unexpected error occurred while loading users.', 'danger')
        return redirect(url_for('register'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        users = User.query.all()
        total_users = len(users)
        
        # Get gender statistics using SQLAlchemy
        gender_stats = db.session.query(
            User.gender, 
            func.count(User.id)
        ).group_by(User.gender).all()
        gender_stats = dict(gender_stats)
        
        # Get latest 5 registered users
        latest_users = User.query.order_by(User.id.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             users=users,
                             total_users=total_users,
                             gender_stats=gender_stats,
                             latest_users=latest_users)
    except Exception as e:
        logger.error(f"Error accessing admin dashboard: {str(e)}")
        flash('Error loading admin dashboard.', 'danger')
        return redirect(url_for('users'))

@app.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Admin status updated for {user.get_full_name()}", 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling admin status: {str(e)}")
        flash('Error updating admin status.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    if not session.get('is_admin') and str(session.get('user_id')) != str(user_id):
        flash('You can only edit your own profile.', 'danger')
        return redirect(url_for('users'))

    try:
        logger.info(f"Accessing edit profile page for user_id: {user_id}")
        user = User.query.get_or_404(user_id)
        form = EditProfileForm(obj=user)
        
        if form.validate_on_submit():
            logger.info(f"Processing profile update for user_id: {user_id}")
            logger.debug(f"Form data received: {form.data}")
            
            try:
                if user.email != form.email.data:
                    logger.info(f"Email change detected: {user.email} -> {form.email.data}")
                    existing_user = User.query.filter(
                        (User.email == form.email.data) & 
                        (User.id != user_id)
                    ).first()
                    
                    if existing_user:
                        logger.warning(f"Email {form.email.data} already registered")
                        flash('Email already registered. Please use another email.', 'danger')
                        return render_template('edit_profile.html', form=form, user=user)

                logger.debug("Starting database transaction for profile update")
                form.populate_obj(user)
                logger.debug(f"Updated user object with form data: {user.first_name} {user.last_name}")
                
                logger.debug("Attempting to commit changes to database")
                db.session.commit()
                logger.info(f"Profile updated successfully for user: {user.user_id}")
                
                # Update session if user updates their own profile
                if session.get('user_id') == user.user_id:
                    session['user_name'] = user.get_full_name()
                
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('users'))
            
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Database integrity error while updating profile: {str(e)}")
                flash('Update failed due to data conflict. Please try again.', 'danger')
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error while updating profile: {str(e)}")
                flash('Database error occurred. Please try again.', 'danger')
        else:
            if request.method == 'POST':
                logger.warning("Form validation failed")
                logger.debug(f"Form errors: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'danger')
        
        return render_template('edit_profile.html', form=form, user=user)
    
    except Exception as e:
        logger.error(f"Error editing profile for user {user_id}: {str(e)}")
        flash('Error updating profile. Please try again.', 'danger')
        return redirect(url_for('users'))

@app.route('/generate_pdf/<int:user_id>')
@login_required
def generate_pdf(user_id):
    if not session.get('is_admin') and str(session.get('user_id')) != str(user_id):
        flash('You can only generate PDF for your own profile.', 'danger')
        return redirect(url_for('users'))

    try:
        user = User.query.get_or_404(user_id)
        html = render_template('user_pdf.html', user=user)
        pdf = pdfkit.from_string(html, False)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=user_{user_id}.pdf'
        return response
    except Exception as e:
        logger.error(f"Error generating PDF for user {user_id}: {str(e)}")
        flash('Error generating PDF. Please try again.', 'danger')
        return redirect(url_for('users'))

# Initialize database if needed
if not init_db():
    logger.critical("Failed to initialize database. Application may not function correctly.")
