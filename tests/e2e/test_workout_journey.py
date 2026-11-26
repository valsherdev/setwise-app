
from playwright.sync_api import Page, expect
from lib.user_repository import UserRepository


def test_complete_workout(page: Page, test_web_address, db_connection):
    # Create a user
    user = UserRepository(db_connection).create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    # Log in
    page.goto(f"{test_web_address}/sessions/new")

    page.get_by_placeholder("Email").fill("test@example.com")
    page.get_by_placeholder("Password").fill("password123")
    page.get_by_role("button", name="Login").click()

    expect(
        page.get_by_role("heading", name=f"Welcome back, {user.username}!")
    ).to_be_visible()

    # Start a workout
    page.get_by_role("button", name="Start workout").click()

    expect(
        page.get_by_text("Workout in progress")
    ).to_be_visible()

    # Select a muscle group
    muscle_group = page.locator("#muscle_group option").nth(1).get_attribute("value")
    page.locator("#muscle_group").select_option(muscle_group)

    # Select an exercise
    exercise = page.locator("#exercise_id option").nth(1)
    exercise_id = exercise.get_attribute("value")
    exercise_name = exercise.inner_text()

    page.locator("#exercise_id").select_option(exercise_id)

    # Add a set
    page.locator("#reps").fill("10")
    page.locator("#weight").fill("20")
    page.get_by_role("button", name="Add set").click()

    expect(page.get_by_role("heading", name=exercise_name)).to_be_visible()
    expect(page.get_by_text("10 reps")).to_be_visible()
    expect(page.get_by_text("at 20 kg")).to_be_visible()

    # Finish the workout
    page.on("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Finish workout").click()

    # Check dashboard and workout history
    expect(
        page.get_by_role("heading", name=f"Welcome back, {user.username}!")
    ).to_be_visible()

    page.get_by_role("link", name="View all").click()

    expect(
        page.get_by_role("heading", name="Workout history")
    ).to_be_visible()

    expect(page.get_by_text("Completed", exact=True)).to_be_visible()



def test_log_past_workout(page: Page, test_web_address, db_connection):
    # Create a user
    user = UserRepository(db_connection).create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    # Log in
    page.goto(f"{test_web_address}/sessions/new")

    page.get_by_placeholder("Email").fill("test@example.com")
    page.get_by_placeholder("Password").fill("password123")
    page.get_by_role("button", name="Login").click()

    expect(
        page.get_by_role("heading", name=f"Welcome back, {user.username}!")
    ).to_be_visible()

    # Log a past workout
    page.locator('input[name="started_at"]').fill("2026-11-25T10:00")
    page.locator('input[name="ended_at"]').fill("2026-11-25T11:00")
    page.locator('textarea[name="notes"]').fill("Upper body session")

    page.get_by_role("button", name="Log workout").click()

    # Check dashboard
    page.goto(f"{test_web_address}/dashboard")

    expect(
        page.get_by_text("Wednesday, 25 November")
    ).to_be_visible()

    # Check workout history
    page.get_by_role("link", name="View all").click()

    expect(
        page.get_by_role("heading", name="Workout history")
    ).to_be_visible()

    expect(page.get_by_text("Completed", exact=True)).to_be_visible()
