from app import myapp, models
from flask import render_template, redirect, request, session, url_for, escape, flash
from .forms import LoginForm, SignUpForm, CreateTripForm
import requests, json, re, datetime

"""
View functions:
* Handle logic on the front-end
* Access the models file to use SQL functions
"""
AMADEUS_API_KEY = 'dqwtFVYJ4Weu6lxZ3uJGffqdrUJYlXFv'
GOOGLE_MAPS_API_KEY = 'AIzaSyD1flhXUIAH853MAQme0Wnak1Hz_ZtgJY4'

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

	# store useful info in the session
	# TODO: I am not sure how to store date object, as storing it
	# as is produces a date non-serializable error, currently
	# converting it to string
	session['date_outbound'] = str(date_outbound)
	session['date_inbound'] = str(date_inbound)
	session['budget'] = budget

	if form.validate_on_submit():
		error = None
		email = session['email']

		# insert the trip into the database and bind the user to the trip
		trip_id = models.create_trip(trip_name, date_outbound, date_inbound, budget)
		models.bind_user_trip(email, trip_id)

		# IMPORTANT! Amadeus API does not support trip search with
		# duration > 15 days, therefore enforcing this artificial restriction
		# otherwise we can remove this
		if get_duration(str(date_outbound), str(date_inbound)) > 15:
			error = 'We currently do not support search of trips with duration longer than 15 days. Please update your search'
			return render_template('createtrip.html', error=error, form=form)

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

	# inputs passed from previous pages
	trip_id = request.args.get('trip_id')
	date_outbound = escape(session['date_outbound'])
	date_inbound = escape(session['date_inbound'])
	budget = escape(session['budget'])

	# user inputs
	destination = request.args.get('destination')

	# on user selected input
	if destination is not None:
		session['destination'] = destination
		models.update_trip(trip_id, 'destination', destination)

		# convert destination into airport
		# TODO: Need to dynamically populate this value
		from_airport = 'SFO'

		# find the closest airport based on the destination
		to_airport = get_nearest_airport(destination)

		# create a placeholder error handling when destination
		# to airport conversion fails
		# in the final product this should never happen,
		# since we will be generating destination based on
		# flight and hotel search
		if to_airport is None:
			error = 'There\'s no nearby airport for the location chosen. Please select a different one'
			render_template('locations.html', trip_id=trip_id, error=error)

		else:
			session['from_airport'] = from_airport
			session['to_airport'] = to_airport
			return redirect(url_for('flights', trip_id=trip_id, destination=destination))

	return render_template('locations.html', trip_id=trip_id, error=error)

# flights
@myapp.route('/flights', methods=['GET','POST'])
def flights():
	error = None

	# inputs passed from previous page
	trip_id = request.args.get('trip_id')
	date_outbound = escape(session['date_outbound'])
	date_inbound = escape(session['date_inbound'])
	budget = escape(session['budget'])
	destination = escape(session['destination'])
	from_airport = escape(session['from_airport'])
	to_airport = escape(session['to_airport'])

	# user inputs
	flight_out = request.args.get('flight_out')
	flight_in = request.args.get('flight_in')

	# fields: from_airport, to_airport, departure_date,
	# duration, n = number of result returned
	data = get_top_flights(from_airport, to_airport,
	departure_date = date_outbound,
	duration = int(get_duration(date_outbound, date_inbound)),
	n = 5)

	# this technically should not happen if we dynamically generate
	# the result for the locations page
	if data is None:
		error = 'Sorry, We did not find any flights that match your criteria, please pick a new location'
		return redirect(url_for('flights', trip_id=trip_id, destination=destination))

	# on user selected input
	if all(i is not None for i in [flight_out, flight_in]):
		# TODO: THIS WILL NEED TO UPDATE THE FLIGHTS TABLE AND THEN PUT THAT ID INTO THE TABLE BELOW!!!!!!!!!!!!!!!!!!!!!
		models.update_trip(trip_id, 'flight_outbound', flight_out)
		models.update_trip(trip_id, 'flight_inbound', flight_in)
		return redirect(url_for('hotels', trip_id=trip_id, destination=destination))

	return render_template('flights.html', trip_id=trip_id, destination=destination, data=data)

# internal helper function
# calculate the date difference in days between two date strings
# returns date_2 - date_1, assuming date 2 >= date 1
# string format YYYY-MM-DD
def get_duration(date_1, date_2):
	 m = re.search('([0-9]+)-([0-9]+)-([0-9]+)', date_1)
	 d1 = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
	 m = re.search('([0-9]+)-([0-9]+)-([0-9]+)', date_2)
	 d2 = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
	 return (d2 - d1).days

# internal helper function
# returns the top n flights given departure and arrival details
# returns None on error
# calls Amadeus API
# TODO: Need to add budget constraint
# TODO: Might need to make 2 calls: one for each leg, currently doing a roundtrip search
def get_top_flights(from_airport, to_airport, departure_date, duration, n):
	url = 'https://api.sandbox.amadeus.com/v1.2/flights/extensive-search'

	params = dict(
	origin=from_airport,
    destination=to_airport,
    departure_date=departure_date,
	duration=duration,
	# one-way='true', # default is false
	# max_price=1000, # default is 950
    apikey=AMADEUS_API_KEY
	)

	try:
		resp = requests.get(url=url, params=params)
		top_n_flights = json.loads(resp.text)['results'][:n]
		return top_n_flights
	except:
		return None

# internal helper function
# returns the nearest airport for a given location, e.g. 'Paris'
# returns None if location cannot be converted to lat, long
# or if there's no airport found near by
# calls Amadeus API
def get_nearest_airport(city):
	location = get_lat_long(city)
	if location is None:
		return None
	else:
		url = 'https://api.sandbox.amadeus.com/v1.2/airports/nearest-relevant'

		params = dict(
		latitude=location['lat'],
		longitude=location['lng'],
		apikey=AMADEUS_API_KEY
		)

		try:
			resp = requests.get(url=url, params=params)
			# the response also has a field called airport, but through
			# trial and error the city field seems to work better :)
			top_airport = json.loads(resp.text)[0]['city']
			return top_airport
		except Error:
			return None

# internal helper function
# returns a dictionary of (lat, long) for a given location, e.g. 'Paris'
# returns None on error
# calls Google Maps API (1000 calls every 24 hours)
def get_lat_long(city):
	url = 'https://maps.googleapis.com/maps/api/geocode/json'

	params = dict(
	address=city,
	key=GOOGLE_MAPS_API_KEY
	)
	try:
		resp = requests.get(url=url, params=params)
		location = json.loads(resp.text)['results'][0]['geometry']['location']
		return location
	except Error:
		return None

# hotels
@myapp.route('/hotels')
def hotels():
	error = None
	trip_id = request.args.get('trip_id')
	destination = request.args.get('destination')
	hotel = request.args.get('hotel')
	print(hotel)
	if hotel is not None:
		# TODO: THIS WILL NEED TO UPDATE THE HOTELS TABLE AND THEN PUT THAT ID INTO THE TABLE BELOW!!!!!!!!!!!!!!!!!!!!!
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
