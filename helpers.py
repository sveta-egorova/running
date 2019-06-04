import json
from functools import wraps

import requests
from flask import redirect, render_template, session, jsonify
from pytz import timezone


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def check_weather(latitude, longitude, timestamp=None):
    """Lookup weather based on GPS coordinates and required timestamp"""

    keyAPI = "011e4db6875ba3e28d705feb6c8c6612"

    # Contact API
    try:
        if timestamp:
            endpoint = f"https://api.darksky.net/forecast/{keyAPI}/{latitude},{longitude},{timestamp}"\
                f"?exclude=minutely,hourly, daily,alerts,flags&units=si"
        endpoint = f"https://api.darksky.net/forecast/{keyAPI}/{latitude},{longitude}"\
            f"?exclude=minutely,hourly, daily,alerts,flags&units=si"
# TODO avoid duplication of links
        response = requests.get(endpoint)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        weather = response.json()
        return {
            "summary": weather["currently"]["summary"],
            "icon": weather["currently"]["icon"],
            "temperature": weather["currently"]["temperature"],
            "humidity": weather["currently"]["humidity"],
            "pressure": weather["currently"]["pressure"],
            "timezone": weather["timezone"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def get_city_list(q):
    """Lookup the list of cities with their attributes based on the user input"""

    # Contact API
    url = f"https://wft-geo-db.p.rapidapi.com/v1/geo/cities?limit=10&namePrefix={q.lower()}"
    headers = {"X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com",
                "X-RapidAPI-Key": "a05c649b91msh43e569e10289861p12ff56jsn045debbbd7bc"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        cities = json.loads(response.content)["data"]
        city_list = [{"value": city["name"] + ", " + city["country"], "latitude": city["latitude"],
                    "longitude": city["longitude"]} for city in cities]
        return jsonify(city_list)
    except (KeyError, TypeError, ValueError):
        return None


def get_location_by_ip(user_ip):
    """Lookup the user current location based on his IP address"""

# Contact API
    url = f"https://ip-geo-location.p.rapidapi.com/ip/{user_ip}?format=json"
    headers = {"X-RapidAPI-Host": "ip-geo-location.p.rapidapi.com",
               "X-RapidAPI-Key": "a05c649b91msh43e569e10289861p12ff56jsn045debbbd7bc"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        location_input = json.loads(response.content)
        location = {"city": location_input["city"]["name"],
                    "country": location_input["country"]["name"],
                    "latitude": location_input["location"]["latitude"],
                    "longitude": location_input["location"]["longitude"]}
        return location
    except (KeyError, TypeError, ValueError):
        return None


def count_calories(run_type, run_pace, weight, seconds):
    # TODO implement MET with dict

    met_pairs = {
        447: 8.3,
        428: 9,
        372: 9.8,
        335: 10.5,
        316: 11,
        298: 11.8,
        279: 11.8,
        260: 12.3,
        242: 12.8,
        223: 14.5,
        205: 16,
        186: 19,
        171: 19.8,
        160: 23
    }

    if run_type == 1:
        for pace, met in met_pairs.items():
            if run_pace >= pace:
                run_met = met

    calories_burnt = round(run_met * weight * seconds / 3600, 0)

    return calories_burnt


def show_duration(total_seconds):
    hours = int(total_seconds / 3600)
    hours_adj = str(hours) if int(hours) > 9 else "0" + str(hours)
    minutes = int((total_seconds - hours * 3600) / 60)
    minutes_adj = str(minutes) if int(minutes) > 9 else "0" + str(minutes)
    seconds = total_seconds - hours * 3600 - minutes * 60
    seconds_adj = str(seconds) if int(seconds) > 9 else "0" + str(seconds)
    duration_string = hours_adj + ":" + minutes_adj + ":" + seconds_adj
    return duration_string

# "01:35:14 min/km"


def show_pace(pace):
    min_per_km = int(pace / 60)
    minutes_adj = str(min_per_km) if int(min_per_km) > 9 else "0" + str(min_per_km)
    seconds_remainder = pace - min_per_km * 60
    seconds_remainder_adj = str(seconds_remainder) if int(seconds_remainder) > 9 else "0" + str(seconds_remainder)
    pace_string = minutes_adj + ":" + seconds_remainder_adj + " min/km"
    return pace_string


def get_user_ip(request):
    # get user IP and find respective location, weather and timezone information
    user_ip = request.remote_addr
    # if the application is run locally, replace the internal IP with the external one
    if user_ip == "127.0.0.1":
        user_ip = "151.36.210.23"
    return user_ip


def get_cur_weather(request):
    user_ip = get_user_ip(request)
    cur_location = get_location_by_ip(user_ip)
    return check_weather(cur_location["latitude"], cur_location["longitude"])


def get_location_string(request):
    user_ip = get_user_ip(request)
    cur_location = get_location_by_ip(user_ip)
    return cur_location["city"] + ", " + cur_location["country"]


def get_cur_timezone(request):
    local_data = get_cur_weather(request)
    return timezone(local_data["timezone"])
