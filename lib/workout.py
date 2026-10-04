class Workout:
    def __init__(self, user_id, started_at, ended_at, notes=None, id=None):
        self.user_id = user_id
        self.started_at = started_at
        self.ended_at = ended_at
        self.notes = notes
        self.id = id

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
