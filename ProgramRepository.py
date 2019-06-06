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

    def get_prog_by_id(self, user_id):
        """Get all programs followed by a particular username"""
        return self.db.execute("SELECT * FROM programs WHERE follower_id = :follower_id", follower_id=user_id)
