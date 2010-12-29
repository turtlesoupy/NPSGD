"""Module containing the main superclass for all models."""
import os
import sys
import uuid
import random
import string
import logging
import subprocess
from email_manager import Email
import shutil

from config import config

class LatexError(RuntimeError): pass
class ModelTask(object):
    """Abstract base class for all user-defined models.

    Users should create models that inherit from this class. It contains _all_ information
    specific to a given model including parameters, attachments, titles and methods for
    producing the e-mails with results.
    """

    abstractModel = "ModelTask"

    #Every model short implement a subset of these
    short_name  = "unspecified_name"
    subtitle    = "Unspecified Subtitle"
    attachments = []

    def __init__(self, emailAddress, taskId, modelParameters={}, failureCount=0, visibleId=None):
        self.emailAddress      = emailAddress
        self.taskId            = taskId
        self.failureCount      = failureCount
        self.modelParameters   = []
        self.visibleId         = visibleId
        if self.visibleId == None:
            self.visibleId = "".join(random.choice(string.letters + string.digits)\
                                    for i in xrange(8))

        self.workingDirectory  = "/var/tmp/npsgd/%s" % str(uuid.uuid4())

        for k,v in modelParameters.iteritems():
            param = self.parameterType(k).fromDict(v)
            setattr(self, param.name, param)
            self.modelParameters.append(param)

        #Recover ordering
        parameterIndexes = dict((e.name, i) for (i,e) in enumerate(self.__class__.parameters))
        self.modelParameters.sort(key=lambda x: parameterIndexes[x.name])

    def createWorkingDirectory(self):
        try:
            os.makedirs(self.workingDirectory, 0777)
        except OSError, e:
            logging.warning(e)

    def parameterType(self, parameterName):
        """Returns an empty version the parameter class for a given parameter name."""

        for pClass in self.__class__.parameters:
            if parameterName == pClass.name:
                return pClass

        return None

    @classmethod
    def fromDict(cls, dictionary):
        emailAddress = dictionary["emailAddress"]
        taskId       = dictionary["taskId"]
        visibleId    = dictionary["visibleId"]
        failureCount = dictionary["failureCount"]

        return cls(emailAddress, taskId, failureCount=failureCount,
                modelParameters=dictionary["modelParameters"], visibleId=visibleId)

    def asDict(self):
        return {
            "emailAddress" :   self.emailAddress,
            "taskId":          self.taskId, 
            "visibleId":       self.visibleId,
            "failureCount":    self.failureCount,
            "modelName":       self.__class__.short_name,
            "modelVersion":    self.__class__.version,
            "modelParameters": dict((p.name, p.asDict()) for p in self.modelParameters)
        }

    def latexBody(self):
        """Returns the body of the LaTeX PDF used to generate result e-mails."""

        return "This is a test for %s" % self.emailAddress

    def latexParameterTable(self):
        """Returns LaTeX markup with a table containing the values for all input parameters."""

        paramRows = "\\\\\n".join(p.asLatexRow() for p in self.modelParameters)
        return """
        \\begin{centering}
        \\begin{tabular*}{5in}{@{\\extracolsep{\\fill}} l l}
        \\textbf{Parameter} & \\textbf{Value} \\\\
        \\hline
        %s
        \\end{tabular*}
        \\end{centering}""" % paramRows

    def textParameterTable(self):
        """Returns an ascii representation of all parameters (e.g. for the body of e-mails)."""

        return "\n".join(p.asTextRow() for p in self.modelParameters)

    def getAttachments(self):
        pdf = self.generatePDF()

        attach = [('results.pdf', pdf)]
        for attachment in self.__class__.attachments:
            with open(os.path.join(self.workingDirectory, attachment)) as f:
                attach.append((attachment, f.read()))

        return attach

    def prepareGraphs(self):
        """A step in the standard model run to prepare output graphs."""
        pass

    def prepareExecution(self):
        """A step in the standard model run to prepare model execution."""
        pass

    def generatePDF(self):
        """Generates a PDF using the LaTeX template, our model's LaTeX body and PDFLatex.""" 

        latex = config.latexResultTemplate.generate(model_results=self.latexBody(), task=self)
        logging.info(latex)

        texPath = os.path.join(self.workingDirectory, "test_task.tex")
        pdfOutputPath = os.path.join(self.workingDirectory, "test_task.pdf")

        with open(texPath, 'w') as f:
            f.write(latex)

        logging.info("Will run PDFLatex %d times", config.latexNumRuns)
        for i in xrange(config.latexNumRuns):
            logging.info("Calling PDFLatex (run %d) to generate pdf output", i+1)
            retCode = subprocess.call([config.pdfLatexPath, "-halt-on-error", texPath], cwd=self.workingDirectory)
            logging.info("PDFLatex terminated with error code %d", retCode)

            if retCode != 0:
                raise LatexError("Bad exit code from latex")

        with open(pdfOutputPath, 'rb') as f:
            pdf = f.read()

        return pdf


    def failureEmail(self):
        """Returns an e-mail object for notifying the user of a failure to execute this model."""
        return Email(self.emailAddress, 
                config.failureEmailSubject.generate(task=self),
                config.failureEmailTemplate.generate(task=self))

    def resultsEmail(self, attachments):
        """Returns an e-mail object for yielding a results e-mail for the user."""
        return Email(self.emailAddress,
                config.resultsEmailSubject.generate(task=self),
                config.resultsEmailBodyTemplate.generate(task=self),
                attachments)

    def runModel(self):
        """Performs model-specific steps for execution."""
        logging.warning("Called default run model - this should be overridden")

    def run(self):
        """Runs the model with parameters, and returns results email object."""

        logging.info("Running default task for '%s'", self.emailAddress)
        self.createWorkingDirectory()
        try:
            self.prepareExecution()
            self.runModel()
            self.prepareGraphs()
            return self.resultsEmail(self.getAttachments())
        finally:
            if os.path.exists(self.workingDirectory):
                shutil.rmtree(self.workingDirectory)
