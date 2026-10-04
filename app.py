import os
from flask import Flask, request, render_template, redirect, session, flash
from lib.database_connection import get_flask_database_connection, DatabaseConnection
from lib.user_repository import UserRepository
from lib.workout_repository import WorkoutRepository
from lib.exercise_repository import ExerciseRepository
from dotenv import load_dotenv
from login_required import login_required_decorator
from flask_bcrypt import Bcrypt


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]



@app.route("/dashboard", methods=["GET"])
@login_required_decorator
def dashboard():
    connection = get_flask_database_connection(app)
    user_repo = UserRepository(connection)
    user = user_repo.find_by_id(session["user_id"])
    exercise_repo = ExerciseRepository(connection)
    exercises = exercise_repo.all()
    return render_template("dashboard.html", user=user, exercises=exercises)


@app.route("/dashboard", methods=["POST"])
@login_required_decorator
def create_workout():
    connection = get_flask_database_connection(app)
    workout_repo = WorkoutRepository(connection)
    workout_details = request.form 
    new_workout = workout_repo.create(workout_details, user_id=session["user_id"])
    if new_workout is False:
        flash("Please fill in all required fields.")
        return redirect("/dashboard")
    



# --- SIGNUP PAGE ---
@app.route("/", methods=["GET"])
def signup():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("signup_form.html")

@app.route("/", methods=["POST"])
def create_user():
    signup_form_data = request.form
    connection = get_flask_database_connection(app)
    user_repo = UserRepository(connection)
    new_user = user_repo.create(signup_form_data)
    if new_user is False:
        return redirect("/sign-up/failed")
    return redirect("/dashboard")


# --- LOGIN PAGE ---
@app.route("/sessions/new", methods=["GET"])
def get_login_form():
    return render_template("login_form.html")

@app.route("/sessions", methods=["POST"])
def create_session():
    login_form_data = request.form
    connection = get_flask_database_connection(app)
    user_repo = UserRepository(connection)
    user = user_repo.find_by_email(login_form_data["email"])
    if user is None:
        return redirect("/sessions/failed")
    if user_repo.check_password(user, login_form_data["password"]):
        session["user_id"] = user.id
        return redirect("/dashboard")
    else:
        return redirect("/sessions/failed")



# --- FAIL PAGES ---
@app.route("/sessions/failed", methods=["GET"])
def login_form_fail():
    return render_template("login_failed.html")

@app.route("/sign-up/failed", methods=["GET"])
def signup_form_fail():
    return render_template("signup_failed.html")



# --- LOGOUT ---
@app.route("/logout", methods=["GET"])
@login_required_decorator
def logout():
    session["user_id"] = None
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))