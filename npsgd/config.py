"""Config module for reading an NPSGD config file.

This module is meant to be a singleton. It is shared across all modules
in the NPSGD package. The particular daemon will call config.loadConfig("...")
on the config object contained in this module and then we will be ready to go
thereafter.
"""
import os
import sys
import logging
import ConfigParser
import tornado.template
import datetime

class ConfigError(RuntimeError): pass
class Config(object):
    """Internal class for handling NPSGD configs."""
    def __init__(self):
        pass

    def setupLogging(self, logPath):
        """Helper method for setting up logging across daemons."""
        lLevel = logging.DEBUG
        lFormat = format="%(asctime)s - %(levelname)s - %(message)s"

        if logPath == "-":
            logging.basicConfig(level=lLevel, format=lFormat)
        else:
            logging.basicConfig(filename=logPath, level=lLevel, format=lFormat)

    def loadConfig(self, configPath):
        """Reads config file and loads templates using Tornado's template module."""

        config = ConfigParser.SafeConfigParser()
        config.read(configPath)

        self.matlabPath               = config.get('Matlab', 'matlabPath')
        self.matlabRequired           = config.getboolean('Matlab', 'required')
        self.pdfLatexPath             = config.get('Latex',  'pdfLatexPath')
        self.latexNumRuns             = config.getint("Latex", "numRuns")
        self.queueFile                = config.get("npsgd", "queueFile")
        self.resultsEmailBodyPath     = config.get("npsgd", "resultsEmailBodyPath")
        self.resultsEmailSubjectPath  = config.get("npsgd", "resultsEmailSubjectPath")
        self.confirmEmailTemplatePath = config.get("npsgd", "confirmEmailTemplatePath")
        self.confirmEmailSubjectPath  = config.get("npsgd", "confirmEmailSubjectPath")
        self.failureEmailTemplatePath = config.get("npsgd", "failureEmailTemplatePath")
        self.failureEmailSubjectPath  = config.get("npsgd", "failureEmailSubjectPath")
        self.confirmationFailedEmailSubjectPath = config.get("npsgd", "confirmationFailedEmailSubjectPath")
        self.confirmationFailedEmailTemplatePath = config.get("npsgd", "confirmationFailedEmailTemplatePath")
        self.lostTaskEmailSubjectPath = config.get("npsgd", "lostTaskEmailSubjectPath")
        self.lostTaskEmailTemplatePath = config.get("npsgd", "lostTaskEmailTemplatePath")
        self.latexResultTemplatePath  = config.get('Latex', 'resultTemplate')
        self.modelTemplatePath        = config.get('npsgd', 'modelTemplatePath')
        self.modelErrorTemplatePath   = config.get('npsgd', 'modelErrorTemplatePath')
        self.confirmTemplatePath      = config.get('npsgd', 'confirmTemplatePath')
        self.confirmedTemplatePath    = config.get('npsgd', 'confirmedTemplatePath')
        self.confirmTimeout           = datetime.timedelta(minutes=config.getint('npsgd', 'confirmTimeout'))
        self.maxJobFailures           = config.getint("npsgd", "maxJobFailures")
        self.keepAliveInterval        = config.getint("npsgd", "keepAliveInterval")
        self.keepAliveTimeout         = config.getint("npsgd", "keepAliveTimeout")
        self.modelScanInterval        = config.getint("npsgd", "modelScanInterval")
        self.queueServerAddress       = config.get("npsgd", "queueServerAddress")
        self.queueServerPort          = config.getint("npsgd", "queueServerPort")
        self.modelDirectory           = config.get("npsgd", "modelDirectory")
        self.htmlTemplateDirectory    = config.get("npsgd", "htmlTemplateDirectory")
        self.emailTemplateDirectory   = config.get("npsgd", "emailTemplateDirectory")
        self.latexTemplateDirectory   = config.get("npsgd", "latexTemplateDirectory")
        self.requestSecret            = config.get("npsgd", "requestSecret")

        self.alreadyConfirmedTemplatePath    = config.get('npsgd', 'alreadyConfirmedTemplatePath')


        if not os.path.exists(self.htmlTemplateDirectory):
            raise ConfigError("HTML template directory '%s' does not exist" % self.htmlTemplateDirectory)

        if not os.path.exists(self.emailTemplateDirectory):
            raise ConfigError("Email template directory '%s' does not exist" % self.emailTemplateDirectory)

        if not os.path.exists(self.latexTemplateDirectory):
            raise ConfigError("Latex template directory '%s' does not exist" % self.latexTemplateDirectory)

        if not os.path.exists(self.modelDirectory):
            raise ConfigError("Model directory '%s' does not exist" % self.modelDirectory)

        tLoader = tornado.template.Loader(self.emailTemplateDirectory)
        self.resultsEmailBodyTemplate = tLoader.load(self.resultsEmailBodyPath)
        self.confirmEmailTemplate     = tLoader.load(self.confirmEmailTemplatePath)
        self.failureEmailTemplate     = tLoader.load(self.failureEmailTemplatePath)
        self.confirmationFailedEmailTemplate = tLoader.load(self.confirmationFailedEmailTemplatePath)
        self.lostTaskEmailTemplate    = tLoader.load(self.lostTaskEmailTemplatePath)
        self.resultsEmailSubject      = tLoader.load(self.resultsEmailSubjectPath)
        self.confirmEmailSubject      = tLoader.load(self.confirmEmailSubjectPath)
        self.failureEmailSubject      = tLoader.load(self.failureEmailSubjectPath)
        self.confirmationFailedEmailSubject = tLoader.load(self.confirmationFailedEmailSubjectPath)
        self.lostTaskEmailSubject     = tLoader.load(self.lostTaskEmailSubjectPath)

        tLoader = tornado.template.Loader(self.latexTemplateDirectory)
        self.latexResultTemplate      = tLoader.load(self.latexResultTemplatePath)

        self.loadEmail(config)
        self.checkIntegrity()

    def loadEmail(self, config):
        self.smtpUsername = config.get("email", "smtpUsername")
        self.smtpPassword = config.get("email", "smtpPassword")
        self.smtpServer   = config.get("email", "smtpServer")
        self.smtpPort     = config.getint("email", "smtpPort")
        self.smtpUseTLS   = config.getboolean("email", "smtpUseTLS")
        self.smtpUseAuth  = config.getboolean("email", "smtpUseAuth")
        self.fromAddress  = config.get("email", "fromAddress")
        self.bcc          = [e.strip() for e in config.get("email", "bcc").split(",") if e.strip() != ""]
        self.cc           = [e.strip() for e in config.get("email", "cc").split(",") if e.strip() != ""]


    def checkIntegrity(self):
        if self.matlabRequired and not os.path.exists(self.matlabPath):
            raise ConfigError("Matlab executable does not exist at '%s'" % self.matlabPath)

        if not os.path.exists(self.pdfLatexPath):
            raise ConfigError("pdflatex executable does not exist at '%s'" % self.pdfLatexPath)
        

config = Config()
