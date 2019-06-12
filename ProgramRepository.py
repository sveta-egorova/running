class ProgramRepository:
    def __init__(self, db):
        self.db = db

    def create_program(self, user_id, prog_name, weeks, description, goal):
        """Add a new program with its main parameters to the database"""
        self.db.execute("INSERT INTO programs (follower_id, author_id, prog_name, weeks, description, goal, status) "
                        "VALUES(:follower_id, :author_id, :prog_name, :weeks, :description, :goal, :status)",
                        follower_id=user_id,
                        author_id=user_id,
                        prog_name=prog_name,
                        weeks=weeks,
                        description=description,
                        goal=goal,
                        status=0)

    def initiate_program(self, user_id, prog_id, date_start, date_end):
        """Update a status of a program for a given user in the database"""

        # check the current status if exists
        cur_status = self.db.execute("SELECT * FROM status WHERE user_id = :user_id AND prog_id = :prog_id",
                                     user_id=user_id,
                                     prog_id=prog_id)
        if cur_status and cur_status[0]["date_start"] == date_start:
            return 0  # value meaning the program already in place and active from a given date
        if cur_status and not cur_status[0]["date_start"] == date_start:
            self.db.execute("UPDATE status SET date_start = :date_start, date_end = :date_end "
                            "WHERE user_id = :user_id AND prog_id = :prog_id",
                            date_start=date_start,
                            date_end=date_end,
                            user_id=user_id,
                            prog_id=prog_id)
        if not cur_status:
            # get the program length
            self.db.execute("INSERT INTO status (user_id, prog_id, status, date_start, date_end) "
                            "VALUES (:user_id, :prog_id, :status, :date_start, :date_end)",
                            user_id=user_id,
                            prog_id=prog_id,
                            status=1,
                            date_start=date_start,
                            date_end=date_end)


    def get_prog_by_id(self, id):
        """Get all programs of a particular id"""
        return self.db.execute("SELECT * FROM programs WHERE id = :id", id=id)


    def get_prog_by_follower_id(self, follower_id):
        """Get all programs followed by a particular username"""
        return self.db.execute("SELECT * FROM programs WHERE follower_id = :follower_id", follower_id=follower_id)


    def get_status_by_id(self, user_id, prog_id):
        """Get the status of a particular program followed by a particular user"""
        return self.db.execute("SELECT * FROM status WHERE user_id = :user_id AND prog_id = :prog_id",
                               user_id=user_id,
                               prog_id=prog_id)

