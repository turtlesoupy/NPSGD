import os
import sys
import glob
import logging

#See Marty Alchin's "A Simple Plugin Framework"
class NPSGDModelMount(type):
    def __init__(cls, name, bases, attrs):
        modelManager.addModel(cls)

class NPSGDModelManager(object):
    def __init__(self):
        self.models = {}

    def modelNames(self):
        return list(self.models.keys())

    def getModel(self, name):
        return self.models[name]

    def addModel(self, cls):
        #Ignore abstract models
        if not hasattr(cls, 'abstractModel') or cls.abstractModel == cls.__name__:
            return

        if not hasattr(cls, 'short_name'):
            logging.critical("Model '%s' lacks a short_name", cls.__name__)
            sys.exit(1)

        if not hasattr(cls, 'parameters'):
            logging.warning("Model '%s' has no parameters", cls.short_name)

        self.models[cls.short_name] = cls

def setupModels():
    """Attempts to do the initial load of all models. Must be called on script startup"""

    model_path = "models/"
    sys.path.append(model_path)
    try:
        sys.dont_write_bytecode = True
        for pyfile in glob.glob("%s/*.py" % model_path):
            importName = os.path.basename(pyfile).rsplit(".", 1)[0]
            module     = __import__(importName)
            logging.info("Found and loaded model '%s'", importName)
    finally:
        sys.dont_write_bytecode = False

modelManager = NPSGDModelManager()
