from app import myapp, models
from flask import render_template, redirect, request, session, url_for, escape, flash
from .forms import LoginForm, SignUpForm, CreateTripForm

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
@myapp.route('/login', methods=['GET','POST'])
def login():
	user = ''
	error = None
	# if already logged in, redirect to the trips overview
	if 'user' in session:
		user = escape(session['user'])
		return redirect('/trips')
	else: # login
		form = LoginForm()
		if form.validate_on_submit():
			error = None
			# user input
			email = form.email.data
			pwd = form.insecure_password.data
			# return user first name only if email, pwd match DB record
			user = models.validate_user(email, pwd)
			if user is not None:
				session['user'] = user
				session['email'] = email
				return redirect('/trips')
			else:
				error = 'Invalid credentials'
	return render_template('login.html', error=error, form=form)

# sign up
@myapp.route('/signup', methods=['GET','POST'])
def signup():
	error = None
	# if already logged in, redirect to the trips overview
	if 'user' in session:
		user = escape(session['user'])
		return redirect('/trips')
	else: # sign up
		form = SignUpForm()
		if form.validate_on_submit():
			error = None
			# user input
			email = form.email.data
			pwd = form.insecure_password.data
			fname = form.fname.data
			lname = form.lname.data
			# insert the user into the database if the email address is not already associated with an account
			if models.retrieve_user_id(email) is None:
				user = models.signup_user(email, fname, lname, pwd)
				return redirect('/login')
			else:
				error = 'An account with that email address already exits.'
	return render_template('signup.html', error=error, form=form)

# create a trip
@myapp.route('/createtrip', methods=['GET','POST'])
def createtrip():
	error = None
	form = CreateTripForm()
	# user Input
	trip_name = form.trip_name.data
	date_outbound = form.date_outbound.data
	date_inbound = form.date_inbound.data
	budget = form.budget.data
	if form.validate_on_submit():
		error = None
		email = session['email']
		# insert the trip into the database and bind the user to the trip
		trip_id = models.create_trip(trip_name, date_outbound, date_inbound, budget)
		models.bind_user_trip(email, trip_id)
		# passes trip_id to the next page via a URL parameter
		return redirect(url_for('locations', trip_id=trip_id))
	else:
		# this makes sure the error message doesn't display if the user hasn't entered any information
		if all(i is None for i in [trip_name, date_outbound, date_inbound, budget]):
			error = None
		else:
			error = 'There is an error with your submission. Please check the fields (particularly the dates!)'
	return render_template('createtrip.html', error=error, form=form)

# locations
@myapp.route('/locations', methods=['GET','POST'])
def locations():
	error = None
	# gets the trip_id URL parameter
	trip_id = request.args.get('trip_id')
	destination = request.args.get('destination')
	if destination is not None:
		models.update_trip(trip_id, 'destination', destination)
		return redirect(url_for('flights', trip_id=trip_id, destination=destination))
	return render_template('locations.html', trip_id=trip_id)

# flights
@myapp.route('/flights', methods=['GET','POST'])
def flights():
	error = None
	# gets URL parameters
	trip_id = request.args.get('trip_id')
	destination = request.args.get('destination')
	flight_out = request.args.get('flight_out')
	flight_in = request.args.get('flight_in')
	if all(i is not None for i in [flight_out, flight_in]):
		# THIS WILL NEED TO UPDATE THE FLIGHTS TABLE AND THEN PUT THAT ID INTO THE TABLE BELOW!!!!!!!!!!!!!!!!!!!!!
		models.update_trip(trip_id, 'flight_outbound', flight_out)
		models.update_trip(trip_id, 'flight_inbound', flight_in)
		return redirect(url_for('hotels', trip_id=trip_id, destination=destination))
	return render_template('flights.html', trip_id=trip_id, destination=destination)

# hotels
@myapp.route('/hotels')
def hotels():
	error = None
	trip_id = request.args.get('trip_id')
	destination = request.args.get('destination')
	hotel = request.args.get('hotel')
	print(hotel)
	if hotel is not None:
		# THIS WILL NEED TO UPDATE THE HOTELS TABLE AND THEN PUT THAT ID INTO THE TABLE BELOW!!!!!!!!!!!!!!!!!!!!!
		models.update_trip(trip_id, 'hotel', hotel)
		return redirect('/trips')
	return render_template('hotels.html', trip_id=trip_id, destination=destination)

# Display a user's current trips
@myapp.route('/trips')
def trips():
	email = session['email']
	trips = models.retrieve_trips(email)
	return render_template('trips.html', trips=trips)

# Cancel a trip
@myapp.route('/cancel_trip/<trip_id>', methods=['GET','POST'])
def cancel_trip(trip_id):
	models.deactivate_trip(trip_id)
	return redirect('/trips')

# homepage
@myapp.route('/home')
def home():
	return render_template('home.html')

# logout
@myapp.route('/logout')
def logout():
	session.pop('user', None)
	flash('You were logged out')
	return redirect(url_for('login'))