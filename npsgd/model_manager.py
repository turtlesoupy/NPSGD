"""Model plug-in loader with versioning support."""
import os
import sys
import imp
import glob
import hashlib
import inspect
import logging
import threading
from npsgd.config import config
from model_task import ModelTask

class InvalidModelError: pass
class ModelManager(object):
    """Model plug-in loader with versioning support."""
    def __init__(self):
        self.modelLock = threading.RLock()
        self.models = {}
        self.latestVersions = {}

    def modelNames(self):
        with self.modelLock:
            return list(n for (n,v) in self.models.keys())

    def modelVersions(self):
        with self.modelLock:
            return list(self.models.keys())

    def getLatestModel(self, name):
        with self.modelLock:
            return self.latestVersions[name]

    def getModel(self, name, version):
        with self.modelLock:
            return self.models[(name, version)]

    def hasModel(self, name, version):
        with self.modelLock:
            return (name, version) in self.models

    def addModel(self, cls, version):
        #Ignore abstract models
        if not hasattr(cls, 'abstractModel') or cls.abstractModel == cls.__name__:
            return

        if not hasattr(cls, 'short_name'):
            raise InvalidModelError("Model '%s' lacks a short_name" % cls.__name__)

        if not hasattr(cls, 'parameters'):
            raise InvalidModelError("Model '%s' has no parameters" % cls.__name__)

        if self.hasModel(cls.short_name, version):
            return

        cls.version = version
        with self.modelLock:
            self.models[(cls.short_name, version)] = cls
            self.latestVersions[cls.short_name] = cls
            logging.info("Found and loaded model '%s', version '%s'", cls.short_name, cls.version)

    def getModelVersion(self, cls):
        sourceCode = inspect.getsource(inspect.getmodule(cls))
        m = hashlib.md5()
        m.update(sourceCode)
        return m.hexdigest()


def loadMembers(mod, version):
    global modelManager
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and obj.__module__ == mod.__name__ and issubclass(obj, ModelTask):
            modelManager.addModel(obj, version)

def setupModels():
    """Attempts to do the initial load of all models. Must be called on script startup"""
    if config.modelDirectory not in sys.path:
        sys.path.append(config.modelDirectory)
    t = 0
    try:
        sys.dont_write_bytecode = True
        for pyfile in glob.glob("%s/*.py" % config.modelDirectory):
            importName = os.path.basename(pyfile).rsplit(".", 1)[0]
            t += 1
            try:
                m = hashlib.md5()
                with open(pyfile) as f:
                    m.update(f.read())

                version = m.hexdigest()
                module = imp.load_source(importName, pyfile)
                loadMembers(module, version)
            except Exception:
                logging.exception("Unable to load model from '%s'" % importName)
                continue
    finally:
        sys.dont_write_bytecode = False

class ModelScannerThread(threading.Thread):
    """Thread for periodically loading new versions of models."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.done = threading.Event()
        self.daemon = True

    def run(self):
        while True:
            self.done.wait(config.modelScanInterval)
            if self.done.isSet():
                break
            logging.debug("Model scanner thread scanning for models")
            setupModels()

modelScannerThread = None
def startScannerThread():
    global modelScannerThread
    modelScannerThread = ModelScannerThread()
    modelScannerThread.start()

modelManager = ModelManager()
