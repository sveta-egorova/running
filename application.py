import datetime
import os
import re
import time
from tempfile import mkdtemp

from cs50 import SQL
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from pytz import timezone
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from HistoryRepository import HistoryRepository
from UserRepository import UserRepository
from helpers import apology, login_required, check_weather, get_city_list, count_calories, \
    show_pace, show_duration, get_cur_timezone, get_cur_weather, get_location_string

# Set the file directory to come from the user side
UPLOAD_FOLDER = 'photos'
# Set allowed file extensions on the user side
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure the directory for uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Ensure responses aren't cached

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///running.db")
userRepo = UserRepository(db)
historyRepo = HistoryRepository(db)


@app.route("/", methods=["GET"])
def index():
    """Show welcome page"""
    if session.get("user_id"):
        return redirect("/main")
    return render_template("index.html")


@app.route("/main", methods=["GET"])
@login_required
def main():
    """Show information about the user's runs"""

    # get user IP and find respective location, weather and timezone information
    user_ip = request.remote_addr
    # if the application is run locally, replace the internal IP with the external one
    if user_ip == "127.0.0.1":
        user_ip = "151.36.210.23"
    location_object = get_location_by_ip(user_ip)
    weather_now = check_weather(location_object["latitude"], location_object["longitude"])
    location_now = location_object["city"] + ", " + location_object["country"]
    user_timezone_string = weather_now["timezone"]

    # based on the user timezone and current time, create a datetime object to reflect on the interface and
    # aggregate runs
    user_timezone_object = timezone(user_timezone_string)
    cur_datetime = datetime.datetime.now(tz=user_timezone_object)
    cur_date = cur_datetime.date()
    cur_week = cur_date.strftime("%W")

    # data about latest run
    runs = historyRepo.get_runs_by_user_id(session["user_id"])
    zero_timestamp = 0
    latest_run = {}
    km_in_month = 0
    km_in_week = 0
    for run in runs:

        # gather information about the run
        run_distance = run["distance"]
        run_timestamp = run["date"]
        run_datetime = datetime.datetime.fromtimestamp(run_timestamp, tz=timezone(run["timezone"]))
        run_date = run_datetime.date()

        # check if the run should be added to total distance of this month
        run_month = run_datetime.month
        if run_month == cur_datetime.month:
            km_in_month += run_distance

        # check if the run should be added to total distance of this week
        run_week = run_date.strftime("%W")
        if run_week == cur_week:
            km_in_week += run_distance

        # find out whether this run is the latest, and initialize object latest_run
        if run_timestamp > zero_timestamp:
            latest_run = {
                "distance": run_distance,
                "calories": run["calories"],
                "pace": show_pace(run["pace"]),
                "date": run_date
            }
            zero_timestamp = run_timestamp

    # find out the number of days elapsed since the last run
    delta_days = cur_date - latest_run["date"]
    delta_message = ""
    if delta_days.days == 0:
        delta_message = "today"
    elif delta_days.days == 1:
        delta_message = "yesterday"
    elif delta_days.days > 1:
        delta_message = f"{delta_days.days} days ago"

    # TODO add data about next run according to the program

    return render_template("main.html",
                           location=location_now,
                           weather=weather_now,
                           latest_run=latest_run,
                           when=delta_message,
                           total_week=km_in_week,
                           total_month=km_in_month)


@app.route("/info", methods=["GET"])
@login_required
def info():
    """Show information about the user"""
    # TODO provide real arguments

    user = userRepo.get_info_by_id(session["user_id"])[0]
    if user["gender"] == 1:
        gender = "male"
    else:
        gender = "female"

    # create birthday as datetime object
    born = datetime.datetime.strptime(user["birthday"], '%Y-%m-%d').date()
    # create current date as datetime object
    timezone_now = get_cur_timezone(request)
    today = datetime.datetime.now(tz=timezone_now).date()

    age = int(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))
# TODO check year difference differently

    activity_level = [
        {"value": 1, "desc": "Sitting / lying all day", "short_desc": "inactive", "activity_index": 1.2},
        {"value": 2, "desc": "Seated work, no exercise", "short_desc": "inactive", "activity_index": 1.3},
        {"value": 3, "desc": "Seated work, light exercise", "short_desc": "moderate", "activity_index": 1.4},
        {"value": 4, "desc": "Moderately physical work, no exercise", "short_desc": "moderate", "activity_index": 1.5},
        {"value": 5, "desc": "Moderately physical work, light exercise", "short_desc": "moderate", "activity_index": 1.6},
        {"value": 6, "desc": "Moderately physical work, heavy exercise", "short_desc": "active", "activity_index": 1.7},
        {"value": 7, "desc": "Heavy work / heavy exercise", "short_desc": "active", "activity_index": 1.8},
        {"value": 8, "desc": "Above average physical work / exercise", "short_desc": "active", "activity_index": 2.0},
    ]

    default_activity_level = 3
    activity_index = default_activity_level
    activity_label = "no data"

    for level in activity_level:
        if level["value"] == user["activity_level"]:
            activity_index = level["activity_index"]
            activity_label = level["short_desc"]
            break

    if user["gender"] == 1:
        bmr_index = int(13.397 * user["weight"] + 4.799 * user["height"] - 5.677 * age + 88.362)
    else:
        bmr_index = int(9.247 * user["weight"] + 3.098 * user["height"] - 4.330 * age + 447.593)

    bmr_adjusted = int(bmr_index * activity_index)

    result = {
        "name": user["name"].upper(),
        "username": user["username"].lower(),
        "gender": gender,
        "age": age,
        "height": user["height"],
        "weight": user["weight"],
        "activity_label": activity_label,
        "bmr": bmr_index,
        "bmr_adj": bmr_adjusted
    }

    return render_template("info.html", data=result)


@app.route("/weather", methods=["GET", "POST"])
@login_required
def weather():
    """Prompts user to choose the city where check weather"""

    # User reached route via GET (as by submitting a form via GET)
    if request.method == "GET":
        return render_template("weather.html")

    # User reached route via POST (as by submitting a form via POST)
    else:
        location = request.form.get("location")
        latitude = request.form.get("city_latitude")
        longitude = request.form.get("city_longitude")
        cur_weather = check_weather(latitude, longitude)
        cur_weather["temperature"] = round(cur_weather["temperature"])
        return render_template("weather-now.html", weather=cur_weather, location=location)
# TODO add units of measure


@app.route("/check-username")
def check_username():
    """Return true if username available, else false, in JSON format"""

    username = request.args.get("username")
    username_valid = userRepo.check_username(username)
    return jsonify(username_valid)


@app.route("/search-location")
def search():
    """Find the list of cities and their respective GPS based on the user's string, in JSON format"""

    q = request.args.get("term")
    return get_city_list(q)


@app.route("/log-run", methods=["GET", "POST"])
@login_required
def log_run():
    """Log the latest training of the user"""

    # User reached route via GET (as by submitting a form via GET)
    if request.method == "GET":
        date = datetime.datetime.now()
        time_now = date.strftime('%d/%m/%Y, %H:%M')
        # print(time_now)
        return render_template("log-run.html", time=time_now)

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure distance was given
        if not request.form.get("distance"):
            return apology("please provide run distance", 403)

        # define running type
        run_type = int(request.form.get("type"))  # string of values 1,2,3
        treadmill = 1 if request.form.get("treadmill") else 0  # string or nonetype

        # create timezone object
        timezone_string = request.form.get("timezone")
        run_timezone = timezone(timezone_string)

        # create datetime object
        run_datetime_string = request.form.get("datetime")  # string
        run_datetime_naive = datetime.datetime.strptime(run_datetime_string, '%Y-%m-%dT%H:%M')

        # combine both datetime and timezone
        run_datetime = run_timezone.localize(run_datetime_naive, is_dst=None)
        run_datetime_unix = int(time.mktime(run_datetime.timetuple()))

        # TODO to check correct date and time of the run on the user interface

        distance = float(request.form.get("distance"))  # string

        # calculate duration and pace
        hours = request.form.get("hours") or 0  # string
        minutes = request.form.get("minutes") or 0  # string
        seconds = request.form.get("seconds") or 0  # string
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        pace = int(total_seconds / distance)

        # TODO autoscroll of numbers

        elevation = int(request.form.get("elevation") or 0)  # string

        heartrate_avg = int(request.form.get("heartrate_avg") or 0)  # string
        heartrate_high = int(request.form.get("heartrate_high") or 0)  # string

        location = request.form.get("location")  # string

        # TODO activate API data upload for temperature and humidity
        latitude = request.form.get("city_latitude")
        longitude = request.form.get("city_longitude")
        cur_weather = check_weather(latitude, longitude)
        temperature = round(cur_weather["temperature"], 0)
        humidity = cur_weather["humidity"]

        # Count calories burnt during the training
        rows = userRepo.get_info_by_id(session["user_id"])
        weight = rows[0]["weight"]
        calories_burnt = count_calories(run_type, pace, weight, total_seconds)

        # Add training to database
        historyRepo.add_run(session["user_id"],
                            run_type,
                            run_datetime_unix,
                            distance,
                            total_seconds,
                            elevation,
                            pace,
                            heartrate_avg,
                            heartrate_high,
                            temperature,
                            humidity,
                            calories_burnt,
                            treadmill,
                            latitude,
                            longitude,
                            timezone_string)

        # Redirect user to home page
        return redirect("/history")


@app.route("/history", methods=["GET"])
@login_required
def see_history():
    """Show the latest training of the user"""

    runs = historyRepo.get_runs_by_user_id(session["user_id"])

    run_types = ["", "running", "walking", "hiking/climbing"]
    result = []
    for run in runs:
        run_timezone = timezone(run["timezone"])
        datetime_object = datetime.datetime.fromtimestamp(run["date"], tz=run_timezone)
        result.append({
            "type": run_types[run["type"]],
            "day": datetime_object.date(),
            "time": datetime_object.time(),
            "duration": show_duration(run["duration"]),
            "pace": show_pace(run["pace"]),
            "distance": run["distance"],
            "calories": run["calories"],
            "elevation": run["elevation"],
            "temperature": run["temperature"],
            "heartrate_avg": run["heartrate_avg"]
        })

    return render_template("history.html",
                           runs=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database by username
        rows = userRepo.get_info_by_username(username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        remember_session(username)

        # Redirect user to home page
        return redirect("/main")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via GET (as by submitting a form via GET)
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        pass_regex = re.compile(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{4,8}$")

        # Ensure username was chosen
        if not request.form.get("username"):
            return apology("please create username", 400)

        # Ensure password was chosen
        if not request.form.get("password"):
            return apology("please provide password", 400)

        # Ensure password matches specified format
        if not pass_regex.search(request.form.get("password")):
            return apology("please provide password in a valid format", 400)

        # Ensure password was confirmed
        if not request.form.get("confirmation"):
            return apology("please confirm password", 400)

        # Ensure control password is similar to main password
        if request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords do not match", 400)

        # Check if username is valid

        username_valid = userRepo.check_username(request.form.get("username"))
        if not username_valid:
            return apology("please choose a different username", 400)

        # Ensure name was given
        if not request.form.get("name"):
            return apology("please provide your name", 400)

        # Encrypt password created
        hash = generate_password_hash(request.form.get("password"))

        # Add user to database
        userRepo.add_user(request.form.get("username"),
                          hash,
                          request.form.get("name"),
                          request.form.get("birthday"),
                          request.form.get("gender"),
                          request.form.get("height"),
                          request.form.get("weight"),
                          request.form.get("activity_level"))

        # Remember which user has logged in
        remember_session(request.form.get("username"))

        # print("test1")

        # save the users pic if provided
        file = request.files['file']

        # print("test2")

        if file and allowed_file(file.filename):
            filename = request.form.get("username") + ".jpg"
            # print("test3")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # print("test4")

        # Redirect user to home page
        return redirect("/main")


@app.route("/logout", methods=["GET"])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def remember_session(username):
    """Remember which user has logged in"""
    rows = userRepo.get_info_by_username(username)
    session["user_id"] = rows[0]["user_id"]


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4662)
