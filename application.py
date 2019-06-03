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
from helpers import apology, login_required, check_weather, get_city_list, count_calories, show_pace, show_duration

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

    return render_template("index.html")


@app.route("/main", methods=["GET"])
@login_required
def main():
    """Show information about the user's runs"""

    return render_template("main.html")


@app.route("/info", methods=["GET"])
@login_required
def info():
    """Show information about the user"""

    return render_template("info.html")


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
# icon can be one of the following: clear-day, clear-night, rain, snow, sleet, wind, fog, cloudy, partly-cloudy-day,
# or partly-cloudy-night


@app.route("/check-username")
def check():
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

        distance = float(request.form.get("distance")) # string

        # calculate duration and pace
        hours = request.form.get("hours") or 0  # string
        minutes = request.form.get("minutes") or 0  # string
        seconds = request.form.get("seconds") or 0  # string
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        pace = int(total_seconds / distance)

        # TODO autoscroll of numbers

        elevation = float(request.form.get("elevation")) or 0  # string

        heartrate_avg = int(request.form.get("heartrate_avg")) or 0  # string
        heartrate_high = int(request.form.get("heartrate_high")) or 0  # string

        location = request.form.get("location")  # string

        # TODO activate API data upload for temperature and humidity
        latitude = request.form.get("city_latitude")
        longitude = request.form.get("city_longitude")
        cur_weather = check_weather(latitude, longitude)
        temperature = round(cur_weather["temperature"],0)
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

    runs = historyRepo.get_runs_by_id(session["user_id"])

    run_types = {"1":"running", "2": "walking", "3": "hiking/climbing"}
    for run in runs:
        run_type = run["type"]
        run["type"] = run_types[str(run_type)]
        run_timezone = timezone(run["timezone"])
        datetime_object = datetime.datetime.fromtimestamp(run["date"], tz=run_timezone)
        run_date = datetime_object.date()
        run["day"] = run_date
        run_time = datetime_object.time()
        run["time"] = run_time
        duration_string = show_duration(run["duration"])
        run["duration"] = duration_string
        pace_string = show_pace(run["pace"])
        run["pace"] = pace_string

    return render_template("history.html",
                           runs=runs)


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
