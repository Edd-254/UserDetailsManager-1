from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp

class RegistrationForm(FlaskForm):
    user_id = StringField('User ID', validators=[
        DataRequired(),
        Length(min=4, max=20),
        Regexp(r'^[A-Za-z0-9]+$', message="User ID must be alphanumeric")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]',
               message="Password must include letters, numbers, and special characters")
    ])
    
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    
    address = TextAreaField('Address', validators=[
        DataRequired()
    ])
    
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\(\d{3}\) \d{3}-\d{4}$', message="Phone number must be in format (XXX) XXX-XXXX")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])

class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    
    address = TextAreaField('Address', validators=[
        DataRequired()
    ])
    
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\(\d{3}\) \d{3}-\d{4}$', message="Phone number must be in format (XXX) XXX-XXXX")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
