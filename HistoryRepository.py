class HistoryRepository:
    def __init__(self, db):
        self.db = db

    def add_run(self, user_id, type, date, distance, duration, elevation, pace, heartrate_avg, heartrate_high,
                location, temperature, humidity, calories):
        """Add a new training to the database"""

        self.db.execute("INSERT INTO trainings (user_id, type, date, distance, duration, elevation, pace, heartrate_avg, "
                        "heartrate_high, location, temperature, humidity, calories) "
                        "VALUES(:user_id, :type, :date, :distance, :duration, :elevation, :pace, :heartrate_avg, "
                        ":heartrate_high, :location, :temperature, :humidity, :calories)",
                        user_id=user_id,
                        type=type,
                        date=date,
                        distance=distance,
                        duration=duration,
                        elevation=elevation,
                        pace=pace,
                        heartrate_avg=heartrate_avg,
                        heartrate_high=heartrate_high,
                        location=location,
                        temperature=temperature,
                        humidity=humidity,
                        calories=calories)


    def get_runs_by_id(self, id):
        """Get all info from a database related to a particular username"""
        return self.db.execute("SELECT * FROM trainings WHERE id = :id", id = id)