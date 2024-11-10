import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash
import pdfkit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

def init_db():
    try:
        logger.info("Attempting to create database tables...")
        with app.app_context():
            # Test database connection
            db.session.execute('SELECT 1')
            logger.info("Database connection successful")
            
            # Create tables
            db.create_all()
            logger.info("Database tables created successfully")
            return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

db.init_app(app)

from models import User
from forms import RegistrationForm

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate():
        try:
            user = User(
                user_id=form.user_id.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                address=form.address.data,
                gender=form.gender.data,
                phone=form.phone.data,
                email=form.email.data
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {user.user_id}")
            flash('Registration successful!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html', form=form)

@app.route('/users')
def users():
    try:
        users = User.query.all()
        return render_template('users.html', users=users)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        flash('Error loading users.', 'danger')
        return redirect(url_for('register'))

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
        flash('Error generating PDF.', 'danger')
        return redirect(url_for('users'))

# Initialize database
if not init_db():
    logger.critical("Failed to initialize database. Application may not function correctly.")
