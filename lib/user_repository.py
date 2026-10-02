from lib.user import User
from psycopg import errors
from flask_bcrypt import generate_password_hash, check_password_hash

class UserRepository:

    def __init__(self, connection):
        self._connection = connection


    def create(self, user):
        try:
            new_user = User(**user)
            if not all([new_user.username, new_user.email, new_user.password]):
                print("Fields cannot be empty")
                return False

            hashed_password = generate_password_hash(new_user.password).decode("utf-8")

            self._connection.execute(
                "INSERT INTO USERS (username, email, password) VALUES (%s, %s, %s)", [
                    new_user.username,
                    new_user.email,
                    hashed_password
                ]
            )

        except errors.UniqueViolation:
            print("Username or email already exists, try again")
            return False
        return None

    
    def find_by_email(self, email):
        try:
            user = self._connection.execute(
                "SELECT * FROM users WHERE email = %s", [email]
                )[0]
        
        except IndexError:
            return None
        return User(**user)


    def check_password(self, user, password):
        return check_password_hash(user.password, password)

