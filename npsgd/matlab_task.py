import os
import logging
import subprocess
from model_task import ModelTask
from config import config

class MatlabError(RuntimeError): pass
class MatlabTask(ModelTask):
    """Abstract base matlab task.

    This class is meant to be the superclass of the user's various
    matlab tasks. It takes parameters from the web interface and
    launches a matlab script with the parameters _directly_
    available in the matlab namespace.
    """

    abstractModel = "MatlabTask"

    #Must specify matlab script

    def runModel(self):
        matlabBase = os.path.dirname(self.matlabScript)
        matlabFun  = os.path.basename(self.matlabScript).rsplit(".",1)[0]

        paramCode = "\n".join(p.asMatlabCode() for p in self.modelParameters)
        io = "%s;\npath('%s', path);\n%s;\nexit;\n" % (paramCode, matlabBase, matlabFun)

        logging.info("Opening matlab with script:\n %s", io)
        mProcess = subprocess.Popen([config.matlabPath, "-nodisplay"], stdin=subprocess.PIPE, cwd=self.workingDirectory)
        mProcess.communicate(io)
        if mProcess.returncode != 0:
            raise MatlabError("Bad return code %s from matlab" % mProcess.returncode)
        logging.info("Matlab all done!")
