from app import myapp, models
from flask import render_template, redirect, request, session, url_for, escape, flash
# from .forms import LoginForm, SignUpForm

"""
View functions:
* Handle logic on the front-end
* Access the models file to use SQL functions
"""

# landing redirect
@myapp.route('/')
@myapp.route('/index')
def index():
	return redirect('/home')

# login
@myapp.route('/login', methods=['GET', 'POST'])
def login():
	return render_template('login.html')

# locations
@myapp.route('/locations')
def locations():
	return render_template('locations.html')

# locations
@myapp.route('/flights')
def flights():
	return render_template('flights.html')

# locations
@myapp.route('/hotels')
def hotels():
	return render_template('hotels.html')

# create a trip
@myapp.route('/createtrip')
def createtrip():
	return render_template('createtrip.html')

# trips
@myapp.route('/trips')
def trips():
	return render_template('trips.html')

# this will display the trip information once we've completed a trip
# @app.route('/display/<trip_id>')
# def display_trip(trip_id):
#     trip = models.get_trip_by_id(trip_id)
#     return render_template('trip.html', trip=trip)

# home
@myapp.route('/home')
def home():
	return render_template('home.html')

# logout
@myapp.route('/logout')
def logout():
	session.pop('user', None)
	flash('You were logged out')
	return redirect(url_for('login'))
