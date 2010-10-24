
class ModelParameter(object):
    pass

class StringParameter(ModelParameter):
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
