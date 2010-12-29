"""Module containing abstract base class for standalone models."""
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
        """Returns parameters to the underlying executable as a Python list."""

        return [
                "-al",
                "*"
        ]

    def runModel(self):
        """Spawns a python subprocess of 'executable' class variable and executes.

        This method is meant to run standalone binaries of models. It stores the
        stdout/stderr in class variables called self.stdout and self.stderr.
        """

        exe = self.__class__.executable

        logging.info("Launching subprocess '%s %s'", exe, " ".join(self.executableParameters()))
        mProcess = subprocess.Popen([exe] + self.executableParameters(),
                cwd=self.workingDirectory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.stdout, self.stderr = mProcess.communicate()
        logging.info("Stdout was: --------\n%s\n-----",  self.stdout)
        logging.info("Stderr was: --------\n%s\n-----",  self.stderr)

        if mProcess.returncode != 0:
            raise ExecutableError("Bad return code '%s' from '%s'" % (mProcess.returnCode, exe))

        logging.info("Subprocess all done")

