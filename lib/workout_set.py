class WorkoutSet:
    def __init__(self, workout_id, exercise_id, set_number, reps, weight, id=None):
        self.workout_id = workout_id
        self.exercise_id = exercise_id
        self.set_number = set_number
        self.reps = reps
        self.weight = weight
        self.id = id

    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__