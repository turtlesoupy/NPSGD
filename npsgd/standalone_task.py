import os
import logging
import subprocess
from model_task import ModelTask
from config import config

class StandaloneError(RuntimeError): pass
class StandaloneTask(ModelTask):
    """Abstract base task for standalone models.

    This class is meant to be the superclass of the user's various
    standalone models. These will generally compiled models, but can include
    anything that needs to be launched in a subprocess
    """

    abstractModel = "StandaloneTask"
    executable    = "ls"

    def executableParameters(self):
        return [
                "-al",
                "*"
        ]

    def runModel(self):
        exe = self.__class__.executable

        logging.info("Launching subprocess '%s %s'", exe, " ".join(self.executableParameters()))
        mProcess = subprocess.Popen([exe] + self.executableParameters(),
                cwd=self.workingDirectory)
        mProcess.wait()

        if mProcess.returncode != 0:
            raise ExecutableError("Bad return code '%s' from '%s'" % (mProcess.returnCode, exe))

        logging.info("Subprocess all done")

