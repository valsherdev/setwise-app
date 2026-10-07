from lib.workout import Workout
from datetime import datetime


class WorkoutRepository:

    def __init__(self, connection):
        self._connection = connection

    def start(self, user_id):
        new_workout = Workout(
            user_id=user_id,
            started_at=datetime.now(),
            ended_at=None,
            notes=None
        )
        result = self._connection.execute(
            "INSERT INTO workouts (user_id, started_at, ended_at, notes) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            [new_workout.user_id, new_workout.started_at,
                new_workout.ended_at, new_workout.notes]
        )
        new_workout.id = result[0]["id"]
        return new_workout

    def log_past(self, workout_data, user_id):
        new_workout = Workout(
            user_id=user_id,
            started_at=workout_data.get("started_at"),
            ended_at=workout_data.get("ended_at"),
            notes=workout_data.get("notes")
        )

        if not new_workout.started_at or not new_workout.ended_at:
            return False
        if new_workout.ended_at < new_workout.started_at:
            return False

        result = self._connection.execute(
            "INSERT INTO workouts (user_id, started_at, ended_at, notes) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            [
                new_workout.user_id,
                new_workout.started_at,
                new_workout.ended_at,
                new_workout.notes
            ]
        )
        new_workout.id = result[0]["id"]
        return new_workout

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

    def find_in_progress(self, user_id):
        rows = self._connection.execute(
            "SELECT * FROM workouts WHERE user_id = %s AND ended_at IS NULL", [
                user_id]
        )
        if not rows:
            return None
        return Workout(**rows[0])
