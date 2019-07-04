# Introduction

RunPal is a web application about running designed for people who wish to keep track of their trainings, create their own running programs, follow these programs and share with others.

# Motivation

What makes this project different from many other similar applications aimed at training logs (e.g. Nike Running, Runtastic, etc) is the possibility to create your own running programs, follow the programs created by others, edit them and use them in a more flexible way.

# Build status

The project is at the phase of continuous integration, bug fixes and features adding.

# Technical description / framework used

The web-application is driven on Flask framework with a backend written in Python using several free APIs (e.g. location by IP-address, geolocation data by coordinates, current and historical weather conditions by coordinates, and timestamp) and a built-in database keeping track of users, runs and programs.

Front-end is mostly based on Bootstrap libraries with a bit of personal touch.

# Code design

The server side is divided into several python files:

- _application.py_ – the main directory used by Flask that outlines the website architecture and the way how the server should respond to different kinds of user requests to different links, as well as correctly handling POST requests and saving information
- _running.db_ – the database file maintaining all information about users, their trainings and programs
- _helpers.py_ – the file containing definition of various functions called from application.py that does not work with the database
- _userRepository.py, historyRepository.py, programHistory.py –_ the files containing definition of various functions called from application.py that deal with the database (respectively, the part including user data, run data, and program data) _ _

# Code example

```python
@app.route("/create-program", methods=["GET", "POST"])
@login_required
def create_program():
    """Create a program"""

    # User reached route via GET (as by submitting a form via GET)
    if request.method == "GET":
        return render_template("create-program.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Add program to database
        programRepo.create_program(session["user_id"],
                                   request.form.get("prog-name"),
                                   int(request.form.get("weeks")),
                                   request.form.get("description"),
                                   int(request.form.get("goal")))

        return redirect("/programs")
```

# Installation

In order to install the project, one should run the command flask run.

# Requirements

- CS50
- Flask
- Flask-Session
- Requests
- Werkzeug
- Pytz

# API reference

The project is using several free APIs:

- [DarkSky]([https://darksky.net/dev](https://darksky.net/dev)) that provides weather conditions on certain time/date at certain location (based on its geo coordinates), used for weather lookup relating to each training and current weather on the user main page
- [GeoDB Cities]([https://rapidapi.com/wirefreethought/api/geodb-cities](https://rapidapi.com/wirefreethought/api/geodb-cities)) that provides the full list of city names, countries and their respective geo coordinates, is used in logging runs where the user is provided with autocomplete form with potential options based on the first letters typed
- [IP Geo Location]([https://rapidapi.com/natkapral/api/ip-geo-location](https://rapidapi.com/natkapral/api/ip-geo-location)) that provides the geo coordinates based on the IP-address of the user when he/she accesses the relevant page

# Some interesting features

Some data about the user are calculated automatically by the program:

- Location of the user reflected on the main page (based on IP-address) and respective weather conditions
- Average pace (based on the run duration and distance)
- Calories burnt (based on the data about the training, calories burnt, certain statutory user data and MET coefficients for different kinds of physical activities)
- Metabolic basal rate (based on user&#39;s statutory data)
- Age (based on user birthday timestamp and current timestamp)
- Weather conditions for each training as reflected in the history page, based on the chosen location and date/time



# External graphics / Front end

- Main picture is taken from personal archives
- Front end is mainly inspired by Bootstrap with certain customization where necessary
- The logo and weather-condition-icons are used from a free source of icons ([https://www.flaticon.com](https://www.flaticon.com))
- The majority of fonts are taken from Google Fonts open source



# How to use (with screenshots)

1. Create account. The system will check whether you choose a valid name and password, then it will redirect the user to the main page. Passwords are securely stored in the encrypted form in a database
 ![pic1](/docs/Picture1.png)
1. If the profile already exists, the user will simply log in using his/her credentials
 ![pic2](/docs/Picture2.png)
1. The user can view the main page with some information about his current location/weather and some running statistics such as details of last run, next run (if the program is activated), and logged runs in the past
 ![pic3](/docs/Picture3.png)
1. The user can add a new run by including the relevant data about it
 ![pic4](/docs/Picture4.png)
1. The user can view the run history in descending order (from the latest to the oldest) that includes, among other things, some automatically generated information, such as average pace, calories burnt, temperature on the street during the run
 ![pic5](/docs/Picture5.png)
1. The user can create a program and the activate/disactivate it, if he wants to start following it from a specific date, and to see reminders on the man page
 ![pic6](/docs/Picture6.png)

# Credits

Big thank you goes to all organizers of CS50 course who opened the new programming world for me, and my dearest Ernest Sadykov who is supporting me in everything that I am doing
