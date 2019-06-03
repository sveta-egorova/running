class UserRepository:
    def __init__(self, db):
        self.db = db

    def add_user(self, username, hash, name, birthday, gender, height, weight, activity_level):
        """Add a new user with his credentials to the database"""
        self.db.execute("INSERT INTO users (username, hash, name, birthday, gender, height, weight, activity_level) "
                        "VALUES(:username, :hash, :name, :birthday, :gender, :height, :weight, :activity_level)",
                username=username,
                hash=hash,
                name=name,
                birthday=birthday,
                gender=gender,
                height=height,
                weight=weight,
                activity_level=activity_level)

    def get_info_by_username(self, username):
        """Get all info from a database related to a particular username"""
        return self.db.execute("SELECT * FROM users WHERE username = :username", username=username)

    def get_info_by_id(self, id):
        """Get all info from a database related to a particular username"""
        return self.db.execute("SELECT * FROM users WHERE user_id = :id", id=id)


    def check_username(self, username):
        """Query database to determine if chosen username is valid"""
        username_exists = self.db.execute("SELECT * FROM users WHERE username = :username",
                                username = username)
        if username_exists or len(username) < 1:
            return False
        else:
            return True

