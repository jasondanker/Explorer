import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash

"""
Database functions:
* Handle information retrieval and database updates
"""

def validate_user(email, pwd):
    """
    Validates provided login information
    Return the user's first name if True
    Return None if False
    """
    result = retrieve_user_info(email)
    # If email address is not found, return None
    if result is None: return None
    else:
        result = result[0]
        # Checks the entered password against the stored hash and passes first_name if successful
        if check_password_hash(result['pw_hash'], pwd):
            return result['first_name']
        # Returns None if not
        else: return None

def signup_user(email, fname, lname, pwd):
    """
    Creates a new user in the db
    Salts and hashes the password
    """
    with sql.connect("app.db") as con:
        # Salts and hashes the users password
        pw_hash = generate_password_hash(pwd)
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "INSERT INTO users (email, first_name, last_name, pw_hash, active) VALUES (?, ?, ?, ?, ?)"
        cur.execute(sql_command, (email, fname, lname, pw_hash, 'TRUE'))
        con.commit()

def create_trip(trip_name, origin, date_outbound, date_inbound, budget):
    """
    Creates a trip entry in the db
    create_trip(trip_name, origin, date_outbound, date_inbound, budget)
    """
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

def create_flight(airline, date_outbound, date_inbound, origin, destination, cost, trip_id):
    """
    Creates a flight entry in the db
    create_flight(airline, date_outbound, date_inbound, origin, destination, cost, trip_id)
    """
    with sql.connect('app.db') as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        'INSERT INTO flights (airline, date_outbound, date_inbound, origin, destination, cost, trip_id, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql_command, (airline, date_outbound, date_inbound, origin, destination, cost, trip_id, 'TRUE'))
        con.commit()
        flight_id = cur.lastrowid # Used to join the user to the trip
        return flight_id # Used to join the user to the trip

def create_hotel(name, check_in, check_out, location, cost, trip_id):
    """
    Creates a hotel entry in the db
    create_hotel(name, check_in, check_out, location, cost, trip_id)
    """
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

def bind_user_trip(email, trip_id):
    """
    Bind a user to a particular trip
    """
    user_id = retrieve_user_id(email)[0]['user_id']
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "INSERT INTO user_trips_junct (user_id, trip_id, active) VALUES (?, ?, ?)"
        cur.execute(sql_command, (user_id, trip_id, 'TRUE'))
        con.commit()

def retrieve_trips(email):
    """
    Retrieve all trips for a user based on their email address
    """
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "SELECT t.trip_id, t.trip_name, t.origin, f.date_outbound, f.date_inbound, t.budget, t.budget_remaining, \
        t.destination, f.airline, h.name \
        FROM trips t JOIN user_trips_junct ut JOIN users u JOIN hotels h JOIN flights f \
        WHERE u.email = '" + email + "' AND \
        u.user_id = ut.user_id AND \
        ut.trip_id = t.trip_id AND \
        h.trip_id = t.trip_id AND \
        f.trip_id = t.trip_id AND \
        t.active = 'TRUE'"
        result = cur.execute(sql_command).fetchall()
    return result

def deactivate_trip(trip_id):
    """
    Set a particular trip_id to inactive
    """
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        update_trips = "UPDATE trips SET active = 'FALSE' WHERE trip_id = " + trip_id
        cur.execute(update_trips)

        update_junct = "UPDATE user_trips_junct SET active = 'FALSE' WHERE trip_id = " + trip_id
        cur.execute(update_junct)
        con.commit()

def update_trip(trip_id, field, value):
    """
    update_trip(trip_id, field, value)
    Update a specified field in a trip with a new value
    """
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')
        sql_command = \
        "UPDATE trips SET " + field + " = '" + value + "' WHERE trip_id = " + str(trip_id)
        cur.execute(sql_command)
        con.commit()

# ---------- Helper Functions ----------

def retrieve_user_info(email):
    """
    Given an email, determine if the user is in the db
    Return their information if found
    Return None if no match is found
    """
    with sql.connect("app.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = ON')

        sql_command = \
        "SELECT first_name, pw_hash \
        FROM users WHERE email = \'" + email + "\'"

        result = cur.execute(sql_command).fetchall()
    if not result:
        return None
    else: return result

def retrieve_user_id(email):
    """
    Given an email, determine if the user is in the db
    Return their user_id if found
    Return None if not found
    """
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
