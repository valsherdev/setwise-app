from lib.workout import Workout

class WorkoutRepository:

    def __init__(self, connection):
        self._connection = connection



    def create(self, workout):
        self._connection.execute(
            "INSERT INTO workouts (user_id, started_at, ended_at, notes) VALUES (%s, %s, %s, %s)",
            [
                workout.user_id,
                workout.started_at,
                workout.ended_at,
                workout.notes
                ]
        )
        return None

    
    def find_by_id(self, workout_id):
        try:
            workout = self._connection.execute(
                "SELECT * FROM workouts WHERE id = %s", [workout_id]
                )[0]
        except IndexError:
            return None

        return Workout(**workout)

    
    def find_by_user_id(self, user_id):
        try:
            workout = self._connection.execute(
                "SELECT * FROM workouts WHERE user_id = %s", [user_id]
                )[0]
        except IndexError:
            return None
         
        return Workout(**workout)