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

