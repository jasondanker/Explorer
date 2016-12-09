from flask.ext.wtf import Form
from wtforms import StringField, IntegerField, PasswordField, SelectField, DateField
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

# create trip form
class CreateTripForm(Form):
    # Could store this in the DB and pull it in here. This would be a more *real* solution but, barring
    # access to a substantial list of IATA codes, isn't necessary at the momemnt.
    origin_list = [('SFO', 'San Francisco, CA'),('OAK', 'Oakland, CA'),('SJC', 'San Jose, CA'),('NYC','New York, NY')]
    trip_name = StringField('trip_name', [validators.required()])
    origin = SelectField('origin', [validators.required()], choices=origin_list)
    date_outbound = DateField('date_outbound', [validators.required()])
    date_inbound = DateField('date_inbound', [validators.required()])
    budget = IntegerField('budget', [validators.required()])