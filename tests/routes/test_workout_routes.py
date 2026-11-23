from datetime import datetime, timezone
from lib.workout_repository import WorkoutRepository


# --- HELPER FUNCTIONS ---
def create_user(db_connection):
    return db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["testuser", "test@example.com", "password123"]
    )[0]["id"]


def login_user(web_client, user_id):
    with web_client.session_transaction() as session:
        session["user_id"] = user_id


# --- TESTS ---
def test_dashboard_access(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    response = web_client.get("/dashboard")

    assert response.status_code == 200


def test_start_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    response = web_client.post("/workouts/start")

    assert response.status_code == 302
    assert response.location.startswith("/workouts/")

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.find_in_progress(user_id)

    assert workout is not None


def test_start_workout_when_one_in_progress(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    existing_workout = workout_repo.start(user_id)

    response = web_client.post("/workouts/start")

    assert response.status_code == 302
    assert response.location == "/dashboard"

    in_progress = workout_repo.find_in_progress(user_id)
    assert in_progress.id == existing_workout.id


def test_log_past_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    response = web_client.post("/workouts/log", data={
        "started_at": "2026-11-15T10:00",
        "ended_at": "2026-11-15T11:00",
        "notes": "Leg day"
    })

    assert response.status_code == 302
    assert response.location.startswith("/workouts/")

    workouts = WorkoutRepository(db_connection).find_by_user_id(user_id)

    assert len(workouts) == 1
    assert workouts[0].notes == "Leg day"
    assert workouts[0].ended_at is not None


def test_log_past_workout_with_missing_times(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    response = web_client.post("/workouts/log", data={
        "started_at": "",
        "ended_at": "",
        "notes": "Leg day"
    })

    assert response.status_code == 302
    assert response.location == "/dashboard"

    assert WorkoutRepository(db_connection).find_by_user_id(user_id) is None


def test_get_individual_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout = WorkoutRepository(db_connection).start(user_id)

    response = web_client.get(f"/workouts/{workout.id}")

    assert response.status_code == 200


def test_get_other_users_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    other_user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["otheruser", "other@example.com", "password123"]
    )[0]["id"]

    login_user(web_client, user_id)
    workout = WorkoutRepository(db_connection).start(other_user_id)

    response = web_client.get(f"/workouts/{workout.id}")

    assert response.status_code == 200
    assert b"Access denied" in response.data


def test_delete_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout = WorkoutRepository(db_connection).start(user_id)

    response = web_client.post(f"/workouts/{workout.id}/delete")

    assert response.status_code == 302
    assert response.location == "/workouts"
    assert WorkoutRepository(db_connection).find_by_id(workout.id) is None


def test_delete_other_users_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    other_user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["otheruser", "other@example.com", "password123"]
    )[0]["id"]

    login_user(web_client, user_id)
    workout = WorkoutRepository(db_connection).start(other_user_id)

    response = web_client.post(f"/workouts/{workout.id}/delete")

    assert response.status_code == 200
    assert WorkoutRepository(db_connection).find_by_id(workout.id) is not None


def test_add_set(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout = WorkoutRepository(db_connection).start(user_id)
    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout.id}/sets",
        data={
            "exercise_id": exercise_id,
            "reps": 10,
            "weight": 20
        }
    )

    assert response.status_code == 302
    assert response.location == f"/workouts/{workout.id}"

    sets = db_connection.execute(
        "SELECT * FROM workout_sets WHERE workout_id = %s",
        [workout.id]
    )

    assert len(sets) == 1
    assert sets[0]["reps"] == 10


def test_add_set_to_completed_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)
    workout_repo.finish(workout.id)

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout.id}/sets",
        data={"exercise_id": exercise_id, "reps": 10}
    )

    assert response.status_code == 302

    sets = db_connection.execute(
        "SELECT * FROM workout_sets WHERE workout_id = %s",
        [workout.id]
    )
    assert len(sets) == 0


def test_edit_set(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout = WorkoutRepository(db_connection).start(user_id)
    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps, weight) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        [workout.id, exercise_id, 1, 10, 20]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout.id}/sets/{set_id}/edit",
        data={"reps": 8, "weight": 25}
    )

    assert response.status_code == 302
    assert response.location == f"/workouts/{workout.id}"

    updated = db_connection.execute(
        "SELECT * FROM workout_sets WHERE id = %s", [set_id]
    )[0]

    assert updated["reps"] == 8
    assert updated["weight"] == 25


def test_delete_set(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout = WorkoutRepository(db_connection).start(user_id)
    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        [workout.id, exercise_id, 1, 10]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout.id}/sets/{set_id}/delete"
    )

    assert response.status_code == 302
    assert response.location == f"/workouts/{workout.id}"

    assert db_connection.execute(
        "SELECT * FROM workout_sets WHERE id = %s", [set_id]
    ) == []


def test_finish_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)

    response = web_client.post(f"/workouts/{workout.id}/finish")

    assert response.status_code == 302
    assert response.location == "/dashboard"

    finished = workout_repo.find_by_id(workout.id)
    assert finished.ended_at is not None


def test_workout_history(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    workout = workout_repo.start(user_id)
    workout_repo.finish(workout.id)

    response = web_client.get("/workouts")

    assert response.status_code == 200


def test_edit_other_users_set(web_client, db_connection):
    user_id = create_user(db_connection)
    other_user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["otheruser", "other@example.com", "password123"]
    )[0]["id"]

    login_user(web_client, user_id)
    other_workout = WorkoutRepository(db_connection).start(other_user_id)

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        [other_workout.id, exercise_id, 1, 10]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{other_workout.id}/sets/{set_id}/edit",
        data={"reps": 20}
    )

    assert response.status_code == 200

    result = db_connection.execute(
        "SELECT reps FROM workout_sets WHERE id = %s", [set_id]
    )[0]
    assert result["reps"] == 10


def test_edit_set_from_different_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    workout1 = workout_repo.start(user_id)
    workout2 = workout_repo.start(user_id)

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        [workout1.id, exercise_id, 1, 10]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout2.id}/sets/{set_id}/edit",
        data={"reps": 20}
    )

    assert response.status_code == 200

    result = db_connection.execute(
        "SELECT reps FROM workout_sets WHERE id = %s", [set_id]
    )[0]
    assert result["reps"] == 10


def test_delete_other_users_set(web_client, db_connection):
    user_id = create_user(db_connection)
    other_user_id = db_connection.execute(
        "INSERT INTO users (username, email, password) "
        "VALUES (%s, %s, %s) RETURNING id",
        ["otheruser", "other@example.com", "password123"]
    )[0]["id"]

    login_user(web_client, user_id)
    other_workout = WorkoutRepository(db_connection).start(other_user_id)

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        [other_workout.id, exercise_id, 1, 10]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{other_workout.id}/sets/{set_id}/delete"
    )

    assert response.status_code == 200

    result = db_connection.execute(
        "SELECT * FROM workout_sets WHERE id = %s", [set_id]
    )
    assert len(result) == 1


def test_delete_set_from_different_workout(web_client, db_connection):
    user_id = create_user(db_connection)
    login_user(web_client, user_id)

    workout_repo = WorkoutRepository(db_connection)
    workout1 = workout_repo.start(user_id)
    workout2 = workout_repo.start(user_id)

    exercise_id = db_connection.execute(
        "SELECT id FROM exercises LIMIT 1"
    )[0]["id"]

    set_id = db_connection.execute(
        "INSERT INTO workout_sets "
        "(workout_id, exercise_id, set_number, reps) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        [workout1.id, exercise_id, 1, 10]
    )[0]["id"]

    response = web_client.post(
        f"/workouts/{workout2.id}/sets/{set_id}/delete"
    )

    assert response.status_code == 200

    result = db_connection.execute(
        "SELECT * FROM workout_sets WHERE id = %s", [set_id]
    )
    assert len(result) == 1