import os
import sys
import logging
import subprocess
import npsgd_model_parameters
from npsgd_model_mount import NPSGDModelMount
from npsgd_model_task import NPSGDModelTask


class NPSGDMatlabTask(NPSGDModelTask):
    abstractModel = "NPSGDMatlabTask"
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
        logging.info("Matlab all done!")
