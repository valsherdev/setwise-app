from lib.exercise import Exercise

class ExerciseRepository:

    def __init__(self, connection):
        self._connection = connection


    def all(self):
        rows = self._connection.execute("SELECT * FROM exercises ORDER BY muscle_group, name")
        return [Exercise(**row) for row in rows]
    

    def find_by_id(self, exercise_id):
        try:
            exercise = self._connection.execute(
                "SELECT * FROM users WHERE id = %s", [exercise_id]
                )[0]
        except IndexError:
                return None
            
        return Exercise(**exercise)