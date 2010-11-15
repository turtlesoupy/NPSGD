import os
import logging
import subprocess
from model_task import ModelTask

class MatlabError(RuntimeError): pass
class MatlabTask(ModelTask):
    abstractModel = "MatlabTask"
    matlabPath    = "/usr/local/MATLAB/R2010b/bin/matlab"
    #Must specify matlab script

    def runModel(self):
        matlabBase = os.path.dirname(self.matlabScript)
        matlabFun  = os.path.basename(self.matlabScript).rsplit(".",1)[0]

        paramCode = "\n".join(p.asMatlabCode() for p in self.modelParameters)
        io = "%s;\npath('%s', path);\n%s;\nexit;\n" % (paramCode, matlabBase, matlabFun)

        logging.info("Opening matlab with script:\n %s", io)
        mProcess = subprocess.Popen([self.matlabPath, "-nodisplay"], stdin=subprocess.PIPE, cwd=self.workingDirectory)
        mProcess.communicate(io)
        if mProcess.returncode != 0:
            raise MatlabError("Bad return code %s from matlab" % mProcess.returncode)
        logging.info("Matlab all done!")
