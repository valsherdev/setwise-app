from lib.workout_set import WorkoutSet

class WorkoutSetRepository:

    def __init__(self, connection):
        self._connection = connection


    
    def find_by_id(self, workout_set_id):
        try:
            workout_set = self._connection.execute(
                "SELECT * FROM workout_sets WHERE id = %s", [workout_set_id]
                )[0]
        except IndexError:
            return None

        return WorkoutSet(**workout_set)