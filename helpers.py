import json
from functools import wraps

import requests
from flask import redirect, render_template, session, jsonify


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


def count_calories(run_type, pace, weight, seconds):
    # TODO implement MET with dict

    met = 0
    if run_type == 1:
        if pace >= 447:
            met = 8.3
        elif pace >= 428:
            met = 9
        elif pace >= 372:
            met = 9.8
        elif pace >= 335:
            met = 10.5
        elif pace >= 316:
            met = 11
        elif pace >= 298:
            met = 11.8
        elif pace >= 279:
            met = 11.8
        elif pace >= 260:
            met = 12.3
        elif pace >= 242:
            met = 12.8
        elif pace >= 223:
            met = 14.5
        elif pace >= 205:
            met = 16
        elif pace >= 186:
            met = 19
        elif pace >= 171:
            met = 19.8
        elif pace >= 160:
            met = 23

    calories_burnt = round(met * weight * seconds / 3600, 0)

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
    minutes_per_km = int(pace / 60)
    seconds_remainder = pace - minutes_per_km * 60
    pace_string = str(minutes_per_km) + ":" + str(seconds_remainder) + " min/km"
    return pace_string
