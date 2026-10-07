from lib.exercise import Exercise


class ExerciseRepository:

    def __init__(self, connection):
        self._connection = connection

    def all(self):
        rows = self._connection.execute(
            "SELECT * FROM exercises ORDER BY muscle_group, name")
        return [Exercise(**row) for row in rows]

    def find_by_id(self, exercise_id):
        try:
            exercise = self._connection.execute(
                "SELECT * FROM exercises WHERE id = %s", [exercise_id]
            )[0]
        except IndexError:
            return None

        return Exercise(**exercise)

    def muscle_groups(self):
        rows = self._connection.execute(
            "SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
        return [row["muscle_group"] for row in rows]

    def find_by_muscle_group(self, muscle_group):
        rows = self._connection.execute(
            "SELECT * FROM exercises WHERE muscle_group = %s ORDER BY name", [muscle_group])
        return [Exercise(**row) for row in rows]
