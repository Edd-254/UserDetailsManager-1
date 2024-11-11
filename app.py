import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import text
import pdfkit
from flask_mail import Mail, Message

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

# Configure Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

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

# Import forms after app initialization
from forms import RegistrationForm, EditProfileForm, RequestPasswordResetForm, ResetPasswordForm

def init_db():
    try:
        logger.info("Starting database initialization...")
        with app.app_context():
            # Test database connection with detailed error handling
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
                # Get list of existing tables
                inspector = db.inspect(db.engine)
                existing_tables = inspector.get_table_names()
                logger.debug(f"Existing tables: {existing_tables}")
                
                # Create tables
                db.create_all()
                logger.info("Database tables created successfully")
                
                # Verify tables were created
                new_tables = db.inspect(db.engine).get_table_names()
                logger.debug(f"Tables after creation: {new_tables}")
                
                return True
            except SQLAlchemyError as e:
                logger.error(f"Failed to create database tables: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Database initialization failed with unexpected error: {str(e)}")
        return False

# Import models after db initialization
from models import User

def send_reset_email(user):
    token = user.generate_reset_token()
    db.session.commit()
    
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    msg.html = render_template('email/reset_password.html',
                             reset_url=reset_url)
    mail.send(msg)

@app.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                send_reset_email(user)
                flash('Reset instructions sent to your email.', 'info')
                return redirect(url_for('register'))
            else:
                flash('Email address not found.', 'danger')
        except Exception as e:
            logger.error(f"Error sending reset email: {str(e)}")
            flash('Error sending reset email. Please try again.', 'danger')
    
    return render_template('request_reset.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.verify_reset_token(token):
            flash('Invalid or expired reset token.', 'danger')
            return redirect(url_for('request_reset'))

        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.password_hash = generate_password_hash(form.password.data)
            user.clear_reset_token()
            db.session.commit()
            flash('Your password has been reset!', 'success')
            return redirect(url_for('register'))
        
        return render_template('reset_password.html', form=form)
    
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        flash('Error resetting password. Please try again.', 'danger')
        return redirect(url_for('request_reset'))

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        logger.info("Processing registration request")
        logger.debug(f"Form data: {form.data}")
        
        if form.validate():
            try:
                # Check if user already exists
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

                # Create new user
                user = User()
                user.user_id = form.user_id.data
                if form.password.data:
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
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('users'))

            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Database integrity error during registration: {str(e)}")
                flash('Registration failed due to data conflict. Please try again.', 'danger')
            except OperationalError as e:
                db.session.rollback()
                logger.error(f"Database connection error during registration: {str(e)}")
                flash('Database connection error. Please try again later.', 'danger')
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error during registration: {str(e)}")
                flash('Registration failed due to database error. Please try again.', 'danger')
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

@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    try:
        logger.info(f"Accessing edit profile page for user_id: {user_id}")
        user = User.query.get_or_404(user_id)
        form = EditProfileForm(obj=user)
        
        if form.validate_on_submit():
            logger.info(f"Processing profile update for user_id: {user_id}")
            logger.debug(f"Form data received: {form.data}")
            
            try:
                # Check if email is being changed and if it's already taken
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

                # Begin transaction
                logger.debug("Starting database transaction for profile update")
                
                # Update user fields using form data
                form.populate_obj(user)
                logger.debug(f"Updated user object with form data: {user.first_name} {user.last_name}")
                
                # Commit changes
                logger.debug("Attempting to commit changes to database")
                db.session.commit()
                logger.info(f"Profile updated successfully for user: {user.user_id}")
                
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
def generate_pdf(user_id):
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