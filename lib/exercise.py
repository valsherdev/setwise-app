class Exercise:
    def __init__(self, name, muscle_group, id=None):
        self.name = name
        self.muscle_group = muscle_group
        self.id = id

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
