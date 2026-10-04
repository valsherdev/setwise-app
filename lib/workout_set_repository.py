from lib.workout_set import WorkoutSet

class WorkoutSetRepository:

    def __init__(self, connection):
        self._connection = connection


    def create(self, set_data, workout_id):
        new_set = WorkoutSet(workout_id=workout_id, **set_data)
        if not all([new_set.exercise_id, new_set.reps]):
            print("Fields cannot be empty")
            return False
        result = self._connection.execute(
            "INSERT INTO workout_sets (workout_id, exercise_id, set_number, reps, weight) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            [new_set.workout_id, new_set.exercise_id, new_set.set_number, new_set.reps, new_set.weight]
        )
        new_set.id = result[0]["id"]
        return new_set

    
    def find_by_id(self, workout_set_id):
        try:
            workout_set = self._connection.execute(
                "SELECT * FROM workout_sets WHERE id = %s", [workout_set_id]
                )[0]
        except IndexError:
            return None

        return WorkoutSet(**workout_set)