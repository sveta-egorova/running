class HistoryRepository:
    def __init__(self, db):
        self.db = db

    def add_run(self, user_id, type, date, distance, duration, elevation, pace, heartrate_avg, heartrate_high,
                temperature, humidity, calories, treadmill, latitude, longitude, timezone):
        """Add a new training to the database"""

        self.db.execute("INSERT INTO trainings (user_id, type, date, distance, duration, elevation, pace, "
                        "heartrate_avg, heartrate_high, temperature, humidity, calories, treadmill, latitude,"
                        "longitude, timezone) "
                        "VALUES(:user_id, :type, :date, :distance, :duration, :elevation, :pace, :heartrate_avg, "
                        ":heartrate_high, :temperature, :humidity, :calories, :treadmill, :latitude, :longitude, "
                        ":timezone)",
                        user_id=user_id,
                        type=type,
                        date=date,
                        distance=distance,
                        duration=duration,
                        elevation=elevation,
                        pace=pace,
                        heartrate_avg=heartrate_avg,
                        heartrate_high=heartrate_high,
                        temperature=temperature,
                        humidity=humidity,
                        calories=calories,
                        treadmill=treadmill,
                        latitude=latitude,
                        longitude=longitude,
                        timezone=timezone)

    def get_runs_by_user_id(self, user_id):
        """Get all info from a database related to a particular username"""
        return self.db.execute("SELECT * FROM trainings "
                               "WHERE user_id = :id "
                               "ORDER BY date DESC",
                               id=user_id)

