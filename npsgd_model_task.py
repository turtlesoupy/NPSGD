import os
import sys
import logging
import subprocess
import npsgd_email
from npsgd_model_manager import NPSGDModelMount

class NPSGDModelTask(object):
    __metaclass__ = NPSGDModelMount
    abstractModel = "NPSGDModelTask"

    @classmethod
    def fromDict(cls, dictionary):
        emailAddress = dictionary["emailAddress"]

        return cls(emailAddress)

    def __init__(self, emailAddress):
        self.emailAddress      = emailAddress
        self.latexPreamblePath = "preamble.tex"
        self.latexFooterPath   = "footer.tex"

    def asDict(self):
        return {
            "emailAddress" : self.emailAddress
        }

    def latexBody(self):
        return "This is a test for %s" % self.emailAddress

    def emailBody(self):
        return "Model run results from NPSG"

    def emailTitle(self):
        return "Model run results from NPSG"

    def generatePDF(self):
        with open(self.latexPreamblePath) as pf:
            preamble = pf.read()
        with open(self.latexFooterPath) as ff:
            footer = ff.read()

        latex = "%s\n%s\n%s" % (preamble, self.latexBody(), footer)
        logging.info(latex)

        workingDirectory = "/var/tmp/npsgd"
        try:
            os.mkdir(workingDirectory)
        except OSError, e:
            pass

        texPath = os.path.join(workingDirectory, "test_task.tex")
        pdfOutputPath = os.path.join(workingDirectory, "test_task.pdf")

        with open(texPath, 'w') as f:
            f.write(latex)

        logging.info("Calling PDFLatex to generate pdf output")
        retCode = subprocess.call(["pdflatex", 
            "-output-directory=%s" % workingDirectory, 
            texPath])
        logging.info("PDFLatex terminated with error code %d", retCode)


        with open(pdfOutputPath, 'rb') as f:
            pdf = f.read()

        return pdf

    def run(self):
        logging.info("Running default task for '%s'", self.emailAddress)
        pdf = self.generatePDF()
        logging.info("Sending results email")
        npsgd_email.sendMessage(self.emailAddress, "NPSG Model Run Results", """
Hi,

This email address recently requested a model run for the NPSG group at the university of
Waterloo. We are happy to report that the run succeeded. We have attached a pdf copy
of the results to this message.

Natural Phenomenon Simulation Group
University of Waterloo
""", [("npsg_results.pdf", pdf)])
        logging.info("Sent!")
