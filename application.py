import re

from tempfile import mkdtemp
from cs50 import SQL
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from helpers import apology, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from UserRepository import UserRepository

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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


@app.route("/")
@login_required
def index():
    """Show information about the user and his runs"""

    return render_template("main.html")

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
        return redirect("/")

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

        # Redirect user to home page
        return redirect("/")


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