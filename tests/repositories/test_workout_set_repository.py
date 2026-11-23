from datetime import datetime, timezone
from lib.workout_set_repository import WorkoutSetRepository

# Helper function
def create_workout(db_connection):
    user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]

    workout_id = db_connection.execute(
        "INSERT INTO workouts (user_id, started_at) "
        "VALUES (%s, %s) RETURNING id",
        [user_id, datetime.now(timezone.utc)]
    )[0]["id"]

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    return workout_id, exercise_id


def test_create(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    workout_set = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 10,
        "weight": 20
    }, workout_id)

    assert workout_set.id is not None
    assert workout_set.workout_id == workout_id
    assert workout_set.exercise_id == exercise_id
    assert workout_set.set_number == 1
    assert workout_set.reps == 10
    assert workout_set.weight == 20


def test_create_increments_set_number(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    first = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 10
    }, workout_id)

    second = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 8
    }, workout_id)

    assert first.set_number == 1
    assert second.set_number == 2


def test_create_without_weight(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    workout_set = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 10,
        "weight": ""
    }, workout_id)

    assert workout_set.weight is None


def test_create_without_exercise_id(db_connection):
    set_repo = WorkoutSetRepository(db_connection)

    result = set_repo.create({"reps": 10}, 1)

    assert result is False


def test_create_without_reps(db_connection):
    set_repo = WorkoutSetRepository(db_connection)

    result = set_repo.create({"exercise_id": 1}, 1)

    assert result is False


def test_find_by_id(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    created = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 10,
        "weight": 20
    }, workout_id)

    workout_set = set_repo.find_by_id(created.id)

    assert workout_set.id == created.id
    assert workout_set.workout_id == workout_id
    assert workout_set.reps == 10


def test_find_by_id_returns_none(db_connection):
    set_repo = WorkoutSetRepository(db_connection)

    assert set_repo.find_by_id(999) is None


def test_find_by_workout_id(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    set_repo.create({"exercise_id": exercise_id, "reps": 10}, workout_id)
    set_repo.create({"exercise_id": exercise_id, "reps": 8}, workout_id)

    workout_sets = set_repo.find_by_workout_id(workout_id)

    assert len(workout_sets) == 2
    assert [s.set_number for s in workout_sets] == [1, 2]


def test_find_by_workout_id_returns_empty_list(db_connection):
    workout_id, _ = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    assert set_repo.find_by_workout_id(workout_id) == []


def test_update(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    created = set_repo.create({
        "exercise_id": exercise_id,
        "reps": 10,
        "weight": 20
    }, workout_id)

    set_repo.update(created.id, {
        "reps": 8,
        "weight": 25
    })

    updated = set_repo.find_by_id(created.id)

    assert updated.reps == 8
    assert updated.weight == 25


def test_delete(db_connection):
    workout_id, exercise_id = create_workout(db_connection)
    set_repo = WorkoutSetRepository(db_connection)

    first = set_repo.create({"exercise_id": exercise_id, "reps": 10}, workout_id)
    second = set_repo.create({"exercise_id": exercise_id, "reps": 8}, workout_id)
    third = set_repo.create({"exercise_id": exercise_id, "reps": 6}, workout_id)

    set_repo.delete(second.id)

    workout_sets = set_repo.find_by_workout_id(workout_id)

    assert len(workout_sets) == 2
    assert [s.id for s in workout_sets] == [first.id, third.id]
    assert [s.set_number for s in workout_sets] == [1, 2]


def test_delete_nonexistent_set(db_connection):
    set_repo = WorkoutSetRepository(db_connection)

    # Should not raise an error
    set_repo.delete(999)