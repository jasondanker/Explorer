from flask.ext.wtf import Form
from wtforms import StringField, IntegerField, PasswordField, SelectField
from flask_wtf.html5 import EmailField
from wtforms import validators

# existing user login form
class LoginForm(Form):
    email = EmailField('username / login email', [validators.required()])
    insecure_password = PasswordField('password', [validators.required()])

# user sign up form
class SignUpForm(Form):
	email = EmailField('username / login email', [validators.required()])
	insecure_password = PasswordField('password', [validators.required()])
	fname = StringField('fname', [validators.required()])
	lname = StringField('lname', [validators.required()])
