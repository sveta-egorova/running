from functools import wraps

import requests
from flask import redirect, render_template, session


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
            "pressure": weather["currently"]["pressure"]
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


def count_calories(run_type, pace, weight, seconds):

    MET = 0
    if run_type == 1:
        if pace >= 447:
            MET = 8.3
        elif pace >= 428:
            MET = 9
        elif pace >= 372:
            MET = 9.8
        elif pace >= 335:
            MET = 10.5
        elif pace >= 316:
            MET = 11
        elif pace >= 298:
            MET = 11.8
        elif pace >= 279:
            MET = 11.8
        elif pace >= 260:
            MET = 12.3
        elif pace >= 242:
            MET = 12.8
        elif pace >= 223:
            MET = 14.5
        elif pace >= 205:
            MET = 16
        elif pace >= 186:
            MET = 19
        elif pace >= 171:
            MET = 19.8
        elif pace >= 160:
            MET = 23
# TODO implement MET with tuples

    calories_burnt = round(MET * weight * seconds / 3600,0)

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
    pace_string = str(minutes_per_km) + ":" + str(seconds_remainder) + "min/km"
    return pace_string
