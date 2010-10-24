import os
import sys
from npsgd_model_mount import NPSGDModelMount
from npsgd_model_task import NPSGDModelTask

matlab_path = "/usr/local/MATLAB/R2010b/bin/matlab"

class NPSGDMatlabTask(NPSGDModelTask):
    abstractModel = "NPSGDMatlabTask"
