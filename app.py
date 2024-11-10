import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text
import pdfkit

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app first
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_only_for_development")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import forms after app initialization
from forms import RegistrationForm, EditProfileForm

def init_db():
    try:
        logger.info("Starting database initialization...")
        with app.app_context():
            # Test database connection with detailed error handling
            try:
                db.session.execute(text('SELECT 1'))
                logger.info("Database connection test successful")
            except SQLAlchemyError as e:
                logger.error(f"Database connection test failed: {str(e)}")
                return False
            
            try:
                # Create tables
                db.create_all()
                logger.info("Database tables created successfully")
                return True
            except SQLAlchemyError as e:
                logger.error(f"Failed to create database tables: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Database initialization failed with unexpected error: {str(e)}")
        return False

# Import models after db initialization
from models import User

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate():
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
            
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered successfully: {user.user_id}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('users'))

        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Database integrity error during registration: {str(e)}")
            flash('Registration failed due to data conflict. Please try again.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error during registration: {str(e)}")
            flash('Registration failed due to database error. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error during registration: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'danger')
    
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
        
        if request.method == 'POST':
            logger.info(f"Processing POST request for user_id: {user_id}")
            form = EditProfileForm(request.form)
            
            if form.validate():
                logger.info("Form validation successful")
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

                    # Update user fields
                    logger.info("Updating user fields")
                    form.populate_obj(user)
                    
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
                logger.warning(f"Form validation failed. Errors: {form.errors}")
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