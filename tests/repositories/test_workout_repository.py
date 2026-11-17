from lib.workout_repository import WorkoutRepository
from datetime import datetime, timezone


def test_start(db_connection):
    result = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )
    user_id = result[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    assert workout.id is not None
    assert workout.user_id == user_id
    assert workout.started_at is not None
    assert workout.ended_at is None
    assert workout.notes is None


def test_log_past(db_connection):
    result = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )
    user_id = result[0]["id"]

    started_at = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
    ended_at = datetime(2026, 11, 15, 11, 0, tzinfo=timezone.utc)

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.log_past({
        "started_at": started_at,
        "ended_at": ended_at,
        "notes": "Leg day"
    }, user_id)

    assert workout.id is not None
    assert workout.user_id == user_id
    assert workout.started_at == started_at
    assert workout.ended_at == ended_at
    assert workout.notes == "Leg day"


def test_log_past_without_start_time(db_connection):
    workout_repo = WorkoutRepository(db_connection)

    workout = workout_repo.log_past({
        "started_at": None,
        "ended_at": datetime(2026, 11, 15, 11, 0, tzinfo=timezone.utc)
    }, 1)

    assert workout is False


def test_log_past_without_end_time(db_connection):
    workout_repo = WorkoutRepository(db_connection)

    workout = workout_repo.log_past({
        "started_at": datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc),
        "ended_at": None
    }, 1)

    assert workout is False


def test_log_past_with_end_time_before_start_time(db_connection):
    workout_repo = WorkoutRepository(db_connection)

    workout = workout_repo.log_past({
        "started_at": datetime(2026, 11, 15, 11, 0, tzinfo=timezone.utc),
        "ended_at": datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
    }, 1)

    assert workout is False


def test_find_by_id(db_connection):
    result = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )
    user_id = result[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    created_workout = workout_repo.start(user_id)

    workout = workout_repo.find_by_id(created_workout.id)

    assert workout.id == created_workout.id
    assert workout.user_id == user_id
    assert workout.started_at is not None
    assert workout.ended_at is None


def test_find_by_id_returns_none(db_connection):
    workout_repo = WorkoutRepository(db_connection)

    assert workout_repo.find_by_id(999) is None


def test_find_by_user_id(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout1 = workout_repo.start(user_id)
    workout2 = workout_repo.start(user_id)

    workouts = workout_repo.find_by_user_id(user_id)

    assert len(workouts) == 2
    assert {w.id for w in workouts} == {workout1.id, workout2.id}


def test_find_by_user_id_returns_none(db_connection):
    workout_repo = WorkoutRepository(db_connection)

    assert workout_repo.find_by_user_id(999) is None


def test_find_in_progress(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    in_progress = workout_repo.find_in_progress(user_id)

    assert in_progress.id == workout.id
    assert in_progress.ended_at is None


def test_find_in_progress_returns_none(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)

    assert workout_repo.find_in_progress(user_id) is None


def test_finish(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    workout_repo.finish(workout.id)

    finished_workout = workout_repo.find_by_id(workout.id)

    assert finished_workout.ended_at is not None
    assert finished_workout.ended_at >= workout.started_at


def test_show_summaries(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)
    workout_repo.finish(workout.id)

    summaries = workout_repo.show_summaries(user_id)

    assert len(summaries) == 1
    assert summaries[0]["id"] == workout.id
    assert summaries[0]["total_sets"] == 0
    assert summaries[0]["exercise_count"] == 0


def test_show_summaries_counts_sets_and_exercises(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    exercise_ids = db_connection.execute(
        "SELECT id FROM exercises LIMIT 2"
    )

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps, weight) "
        "VALUES (%s, %s, %s, %s, %s), "
        "(%s, %s, %s, %s, %s), "
        "(%s, %s, %s, %s, %s)",
        [
            workout.id, exercise_ids[0]["id"], 1, 10, 20,
            workout.id, exercise_ids[0]["id"], 2, 8, 20,
            workout.id, exercise_ids[1]["id"], 1, 12, 15
        ]
    )

    workout_repo.finish(workout.id)
    summaries = workout_repo.show_summaries(user_id)

    assert summaries[0]["total_sets"] == 3
    assert summaries[0]["exercise_count"] == 2


def test_show_summaries_returns_newest_first(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    older = workout_repo.start(user_id)
    newer = workout_repo.start(user_id)

    workout_repo.finish(older.id)
    workout_repo.finish(newer.id)

    summaries = workout_repo.show_summaries(user_id)

    assert summaries[0]["id"] == newer.id
    assert summaries[1]["id"] == older.id


def test_show_summaries_respects_limit(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)

    for _ in range(3):
        workout = workout_repo.start(user_id)
        workout_repo.finish(workout.id)

    summaries = workout_repo.show_summaries(user_id, limit=2)

    assert len(summaries) == 2


def test_show_summaries_returns_empty_list(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)

    assert workout_repo.show_summaries(user_id) == []


def test_delete(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    workout_repo.delete(workout.id)

    assert workout_repo.find_by_id(workout.id) is None