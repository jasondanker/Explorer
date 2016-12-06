AMADEUS_API_KEY = 'dqwtFVYJ4Weu6lxZ3uJGffqdrUJYlXFv'
GOOGLE_MAPS_API_KEY = 'AIzaSyD1flhXUIAH853MAQme0Wnak1Hz_ZtgJY4'
import requests, json, re, datetime

##############################
# TIME HELPER FUNCTIONS
##############################
def get_duration(date_1, date_2):
    """
    calculate the date difference in days between two date strings
    returns date_2 - date_1, assuming date 2 >= date 1
    string format YYYY-MM-DD
    """
    m = re.search('([0-9]+)-([0-9]+)-([0-9]+)', date_1)
    d1 = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search('([0-9]+)-([0-9]+)-([0-9]+)', date_2)
    d2 = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (d2 - d1).days

##############################
# LOCATION HELPER FUNCTIONS
##############################
def get_destinations(origin, budget, date_outbound, date_inbound):
    """
    get a list of destinations given the budget and date input
    """
    # get the list of potential destinations based on flight costs
    potential_destinations, costs = get_potential_destinations(
    origin, budget, date_outbound, date_inbound)

    if potential_destinations is None: return []

    destinations = []
    for i, destination in enumerate(potential_destinations):
        flight_cost = costs[i]
        remaining_budget = float(budget) - flight_cost
        hotel_cost = get_min_hotel_cost(destination, date_outbound, date_inbound, remaining_budget)

        if hotel_cost is not None:
            cost = hotel_cost + flight_cost
            if cost <= budget:
                destinations.append(destination)
    return destinations

def get_location_name(iata_code):
    """
    given an airport IATA code, return the city/area name
    that airport is associated with
    """

    url = 'https://api.sandbox.amadeus.com/v1.2/location/' + iata_code

    params = dict(apikey=AMADEUS_API_KEY)

    resp = requests.get(url=url, params=params)
    data = json.loads(resp.text)['airports'][0]

    # retrive the airport's city name, state and country information
    raw_location = data['city_name'] + ' ' + data['state'] + ' ' + data['country']

    # disambiguate confusing airports like EWR (Newark airport in NJ for NYC)
    state, country = verify_state_country(raw_location)
    return data['city_name'] + ', ' + state + ', ' + country

def verify_state_country(raw_location):
    """
    some locations returned from Amadeus inspiration search is ambiguous,
    e.g. EWR returns New York City, NJ, US
    this function corrects the state and country information
    and returns a consistent address
    """
    url = 'https://maps.googleapis.com/maps/api/geocode/json'

    params = dict(
    address=raw_location,
    key=GOOGLE_MAPS_API_KEY
    )

    resp = requests.get(url=url, params=params)
    address_components = json.loads(resp.text)['results'][0]['address_components']

    state = [component['long_name'] for component in address_components
    if component['types'][0] == 'administrative_area_level_1'][0]

    country = [component['short_name'] for component in address_components
    if component['types'][0] == 'country'][0]

    return state, country

def get_lat_long(city):
    """
    internal helper function
    returns a dictionary of (lat, long) for a given location, e.g. 'Paris'
    returns None on error
    calls Google Maps API (1000 calls every 24 hours)
    """

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

##############################
# FLIGHTS
##############################
def get_top_flights(from_airport, to_airport, departure_date, duration, budget, n):
    """
    returns the top n flights given departure and arrival details
    returns None on error
    calls Amadeus API
    """
    url = 'https://api.sandbox.amadeus.com/v1.2/flights/extensive-search'

    params = dict(
    origin=from_airport,
    destination=to_airport,
    departure_date=departure_date,
    duration=duration,
    # one-way='true', # default is false
    max_price=budget, # default is 950
    apikey=AMADEUS_API_KEY
    )

    try:
        resp = requests.get(url=url, params=params)
        top_n_flights = json.loads(resp.text)['results'][:n]
        return top_n_flights
    except:
        return None

def get_nearest_airport(city):
    """
    returns the nearest airport for a given location, e.g. 'Paris'
    returns None if location cannot be converted to lat, long
    or if there's no airport found near by
    calls Amadeus API
    """
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

def get_potential_destinations(origin, budget, date_outbound, date_inbound, n=10):
    """
    return a list of potential locations given a budget and date duration
    origin needs to be a valid IATA code
    """
    url = 'https://api.sandbox.amadeus.com/v1.2/flights/inspiration-search'

    params = dict(
    origin=origin,
    departure_date=date_outbound,
    duration=int(get_duration(date_outbound, date_inbound)),
    max_price=budget,
    apikey=AMADEUS_API_KEY
    )
    resp = requests.get(url=url, params=params)
    try:
        results = json.loads(resp.text)['results'][:n]
        destinations, costs = [], []
        for result in results:
            destinations.append(get_location_name(result['destination']))
            costs.append(float(result['price']))
        return destinations, costs
    except:
        return None, None


##############################
# HOTELS
##############################
def get_top_hotels(arrival_date, departure_date, destination, budget, n):
    """
    get top n hotels at destination under the given budget and travel dates
    """
    location = get_lat_long(city=destination) # uses yiyi's get_lat_long helper function
    if location is None:
        return None
    else:
        url = 'https://api.sandbox.amadeus.com/v1.2/hotels/search-circle'

        params = dict(
        latitude=location['lat'],
        longitude=location['lng'],
        radius='10',
        check_in=arrival_date,
        check_out=departure_date,
        max_rate=budget,
        apikey=AMADEUS_API_KEY
        )

        try:
        # show the cheapest hotels result. Hotel name, city and total cost
            resp = requests.get(url=url, params=params)
            data = json.loads(resp.text)
            result = [{'property_name': result['property_name'], 'city': result['address']['city'], 'price': result['total_price']['amount']} for result in data['results'][:n]]
            return None if len(result) == 0 else result
        except:
            return None

def get_min_hotel_cost(destination, date_outbound, date_inbound, remaining_budget):
    """
    given the destination and remaining budget, return the minimum hotel cost
    """
    data = get_top_hotels(date_outbound, date_inbound, destination, remaining_budget, n = 1)
    min_cost = None if data is None else float(data[0]['price'])
    return min_cost
