from app import myapp, models
from flask import render_template, redirect, request, session, url_for, escape, flash
from .forms import LoginForm, SignUpForm, CreateTripForm
import requests, json, re, datetime
from app import utils

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
    error = request.args.get('error')
    form = CreateTripForm()

    # user Input
    trip_name = form.trip_name.data
    origin = form.origin.data
    date_outbound = form.date_outbound.data
    date_inbound = form.date_inbound.data
    budget = form.budget.data

    # store useful info in the session
    session['origin'] = origin
    session['date_outbound'] = str(date_outbound)
    session['date_inbound'] = str(date_inbound)
    session['budget'] = budget
    session['trip_name'] = trip_name
    trip_id = 0

    if form.validate_on_submit():
        error = None

        # IMPORTANT! Amadeus API does not support trip search with
        # duration > 15 days, therefore enforcing this artificial restriction
        # otherwise we can remove this
        if utils.get_duration(str(date_outbound), str(date_inbound)) > 15:
            error = 'We currently do not support search of trips with duration longer than 15 days. Please update your search'
            return render_template('createtrip.html', error=error, form=form)

        # passes trip_id to the next page via a URL parameter
        return redirect(url_for('locations'))

    elif any(field is not None for field in [trip_name, date_outbound, date_inbound, budget]):
        # only display error message if the user has entered incomplete (but not empty) information
        error = 'There is an error with your submission. Please check the fields (particularly the dates!)'

    return render_template('createtrip.html', error=error, form=form)

# locations
@myapp.route('/locations', methods=['GET','POST'])
def locations():
    error = request.args.get('error')

    # inputs passed from previous pages
    # trip_id = request.args.get('trip_id')
    date_outbound = session['date_outbound']
    date_inbound = session['date_inbound']
    budget = session['budget']
    origin = session['origin']

    # user inputs
    selected_destination = request.args.get('destination')

    # get a list of destinations
    destinations = utils.get_destinations(origin, budget, date_outbound, date_inbound)

    # if there are no possible destinations with the input budget + date combination,
    # prompt the users to enter different search criteria
    if len(destinations) == 0:
        error = 'We didn\'t find anything matching your criteria. Please select a different date or enter a larger budget'
        return redirect(url_for('createtrip', error=error))

    # on user selected input
    if selected_destination is not None:
        session['destination'] = selected_destination

        # convert destination into airport
        from_airport = origin

        # find the closest airport based on the destination
        to_airport = utils.get_nearest_airport(selected_destination)

        # create a placeholder error handling when destination
        # to airport conversion fails
        # in the final product this should never happen,
        # since we will be generating destination based on
        # flight and hotel search
        if to_airport is None:
            error = 'There\'s no nearby airport for the location chosen. Please select a different one'
            render_template('locations.html',error=error)

        else:
            session['from_airport'] = from_airport
            session['to_airport'] = to_airport
            return redirect(url_for('flights'))

    return render_template('locations.html', error=error, destinations=destinations)

# flights
@myapp.route('/flights', methods=['GET','POST'])
def flights():
    error = request.args.get('error')

    # inputs passed from previous page
    date_outbound = session['date_outbound']
    date_inbound = session['date_inbound']
    budget = session['budget']
    destination = session['destination']
    from_airport = session['from_airport']
    to_airport = session['to_airport']

    # user inputs
    airline_chosen = request.args.get('airline')

    # fields: from_airport, to_airport, departure_date,
    # duration, n = number of result returned
    data = utils.get_top_flights(from_airport, to_airport,
    departure_date = date_outbound,
    duration = int(utils.get_duration(date_outbound, date_inbound)),
    budget = int(budget),
    n = 5)

    # on user selected inputs
    if airline_chosen is not None:

        # update budget with airline cost
        cost = float(request.args.get('cost'))
        budget -= cost
        session['budget_remaining'] = budget
        session['flight_cost'] = '{0:.3f}'.format(cost)
        session['airline'] = airline_chosen

        return redirect(url_for('hotels', destination=destination))

    # this technically should not happen if we dynamically generate
    # the result for the locations page
    if data is None:
        try:
            session.pop('destination', None)
            error = 'Sorry, We did not find any flights that match your criteria, please pick a new location'
            return redirect(url_for('locations', error=error))
        except:
            return redirect(url_for('locations'))

    return render_template('flights.html', destination=destination, data=data, error=error)

# hotels
@myapp.route('/hotels', methods=['GET','POST'])
def hotels():
    error = None

    # date info
    date_outbound = session['date_outbound']
    date_inbound = session['date_inbound']

    # budget and remaining budget info
    budget = session['budget']
    remaining_budget = session['budget_remaining']
    flight_cost = session['flight_cost'] # cost of a single flight

    # location info
    trip_name = session['trip_name']
    origin = session['origin']
    destination = session['destination']
    airline = session['airline']
    to_airport = session['to_airport']

    email = session['email']

    # user input
    hotel_chosen = request.args.get('hotel')

    if hotel_chosen is not None:
        check_in = date_outbound
        check_out = date_inbound
        location = request.args.get('location')
        cost = float(request.args.get('cost'))

    # uses inputs from above
    duration = int(utils.get_duration(date_outbound, date_inbound))
    data = utils.get_top_hotels(arrival_date=date_outbound,
    departure_date=date_inbound,
    destination=destination,
    budget=float(remaining_budget)/duration,
    n = 5)

    if hotel_chosen is not None:
        # DB updates
        # update trip db and link to user ID
        trip_id = models.create_trip(trip_name, origin, date_outbound, date_inbound, budget)
        models.bind_user_trip(email, trip_id)
        models.update_trip(trip_id, 'destination', destination)

        # update flight db and flight info of the corresponding trip
        flight_id = models.create_flight(airline,
        date_outbound, date_inbound, destination, to_airport, 
        flight_cost, trip_id)

        models.update_trip(trip_id, 'flight_id', str(flight_id))

        # update hotel db and hotel info of the corresponding trip
        hotel = models.create_hotel(hotel_chosen, check_in, check_out, location, cost, trip_id)
        models.update_trip(trip_id, 'hotel', str(hotel))

        # update budget info of the corresponding trip
        remaining_budget -= cost
        session['budget_remaining'] = remaining_budget
        models.update_trip(trip_id, 'budget_remaining', '{0:.3f}'.format(remaining_budget))

        # pop all sesssion data
        session.pop('date_outbound', None)
        session.pop('date_inbound', None)
        session.pop('budget', None)
        session.pop('budget_remaining', None)
        session.pop('flight_cost', None)
        session.pop('trip_name', None)
        session.pop('origin', None)
        session.pop('destination', None)
        session.pop('airline', None)
        session.pop('to_airport', None)

        return redirect(url_for('trips'))

    if data is None:
        try:
            session.pop('budget_remaining', None)
            error = 'Sorry, We did not find any hotels that match your criteria, please revise your search.'
            return redirect(url_for('flights', error=error))
        except:
            return redirect(url_for('flights'))

    return render_template('hotels.html', destination=destination, data=data)

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
    if 'user' in session:
        user = escape(session['user'])
        return redirect('/trips')
    else:
        return render_template('home.html')

# logout
@myapp.route('/logout')
def logout():
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('login'))
