import sqlite3 as sql

"""
Database functions:
* Handle information retrieval and database updates
"""

# Login
def validate_user(email, pwd):
    result = retrieve_user_info(email)
    if result is None: return None
    else:
        result = result[0]
        if result['insecure_password'] == pwd:
            return result['first_name']
        else: return None

# Sign Up
def signup_user(email, fname, lname, pwd):
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        sql_command = \
        "INSERT INTO users (email, first_name, last_name, insecure_password, active) VALUES (?, ?, ?, ?, ?)"

        cur.execute(sql_command, (email, fname, lname, pwd, 'TRUE'))
        con.commit()

# Create Trip
def create_trip(trip_name, origin, date_outbound, date_inbound, budget):
    with sql.connect('app.db') as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        'INSERT INTO trips (trip_name, origin, date_outbound, date_inbound, budget, budget_remaining, active) VALUES (?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql_command, (trip_name, origin, date_outbound, date_inbound, budget, budget, 'TRUE'))
        con.commit()
        trip_id = cur.lastrowid # Used to join the user to the trip
        return trip_id # Used to join the user to the trip

# Create Flight
def create_flight(airline, flight_num, flight_date, origin, destination, cost, trip_id):
    with sql.connect('app.db') as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        'INSERT INTO flights (airline, flight_number, flight_date, origin, destination, cost, trip_id, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql_command, (airline, flight_num, flight_date, origin, destination, cost, trip_id, 'TRUE'))
        con.commit()
        flight_id = cur.lastrowid # Used to join the user to the trip
        return flight_id # Used to join the user to the trip

def create_hotel(name, check_in, check_out, location, cost, trip_id):
    with sql.connect('app.db') as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        'INSERT INTO hotels (name, check_in, check_out, location, cost, trip_id, active) VALUES (?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql_command, (name, check_in, check_out, location, cost, trip_id, 'TRUE'))
        con.commit()
        flight_id = cur.lastrowid # Used to join the user to the trip
        return flight_id # Used to join the user to the trip

# bind user with trip information
def bind_user_trip(email, trip_id):
    user_id = retrieve_user_id(email)[0]['user_id']
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "INSERT INTO user_trips_junct (user_id, trip_id, active) VALUES (?, ?, ?)"
        cur.execute(sql_command, (user_id, trip_id, 'TRUE'))
        con.commit()

# Display Trips
# Retrieve all trips for a user by their email address
def retrieve_trips(email):
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "SELECT t.trip_id, t.trip_name, t.origin, t.date_outbound, t.date_inbound, t.budget, t.budget_remaining, \
        t.destination, t.flight_outbound, t.flight_inbound, t.hotel \
        FROM trips t JOIN user_trips_junct ut JOIN users u \
        WHERE u.email = '" + email + "' AND \
        u.user_id = ut.user_id AND \
        ut.trip_id = t.trip_id AND \
        t.active = 'TRUE'"
        result = cur.execute(sql_command).fetchall()
    return result

# Deactivate trip
def deactivate_trip(trip_id):
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        update_trips = "UPDATE trips SET active = 'FALSE' WHERE trip_id = " + trip_id
        cur.execute(update_trips)

        update_junct = "UPDATE user_trips_junct SET active = 'FALSE' WHERE trip_id = " + trip_id
        cur.execute(update_junct)
        con.commit()

# Update a trip with new information
def update_trip(trip_id, field, value):
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "UPDATE trips SET " + field + " = '" + value + "' WHERE trip_id = " + str(trip_id)
        cur.execute(sql_command)
        con.commit()

# ---------- Helper Functions ----------

# retrieve password and first name of a user given their email address
def retrieve_user_info(email):
    # SQL statement to query database goes here
    # Returns None if no match is found
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        sql_command = \
        "SELECT first_name, insecure_password \
        FROM users WHERE email = \'" + email + "\'"

        result = cur.execute(sql_command).fetchall()
    if not result:
        return None
    else: return result

# retrieve ID of a user given their email address
def retrieve_user_id(email):
    # SQL statement to query database goes here
    # Returns None if no match is found
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        sql_command = \
        "SELECT user_id \
        FROM users WHERE email = \'" + email + "\'"

        result = cur.execute(sql_command).fetchall()
    if not result:
        return None
    else: return result
