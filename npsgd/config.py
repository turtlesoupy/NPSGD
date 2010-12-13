import os
import sys
import logging
import ConfigParser
import tornado.template


class ConfigError(RuntimeError): pass
class Config(object):
    def __init__(self):
        pass

    def setupLogging(self, logName):
        logFilename = os.path.join(config.loggingDirectory, logName)
        logging.basicConfig(filename=os.path.join(config.loggingDirectory, logName),\
                            level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    def loadConfig(self, configPath):
        config = ConfigParser.SafeConfigParser()
        config.read(configPath)

        self.matlabPath     = config.get('Matlab', 'matlabPath')
        self.matlabRequired = config.getboolean('Matlab', 'required')
        self.pdfLatexPath   = config.get('Latex',  'pdfLatexPath')
        self.resultsEmailBodyPath     = config.get("npsgd", "resultsEmailBodyPath")
        self.confirmEmailTemplatePath = config.get("npsgd", "confirmEmailTemplatePath")
        self.failureEmailTemplatePath = config.get("npsgd", "failureEmailTemplatePath")
        self.confirmEmailSubject      = config.get("npsgd", "confirmEmailSubject")
        self.latexResultTemplatePath  = config.get('Latex', 'resultTemplate')
        self.modelTemplatePath        = config.get('npsgd', 'modelTemplatePath')
        self.confirmTemplatePath      = config.get('npsgd', 'confirmTemplatePath')
        self.confirmedTemplatePath    = config.get('npsgd', 'confirmedTemplatePath')
        self.resultsEmailSubject      = config.get("npsgd", "resultsEmailSubject")
        self.failureEmailSubject      = config.get("npsgd", "failureEmailSubject")
        self.maxJobFailures           = config.getint("npsgd", "maxJobFailures")
        self.keepAliveInterval        = config.getint("npsgd", "keepAliveInterval")
        self.keepAliveTimeout         = config.getint("npsgd", "keepAliveTimeout")
        self.queueServerAddress       = config.get("npsgd", "queueServerAddress")
        self.queueServerPort          = config.getint("npsgd", "queueServerPort")
        self.loggingDirectory         = config.get("npsgd", "loggingDirectory")
        self.modelDirectory           = config.get("npsgd", "modelDirectory")
        self.templateDirectory        = config.get("npsgd", "templateDirectory")


        if not os.path.exists(self.templateDirectory):
            raise ConfigError("Template directory '%s' does not exist" % self.templateDirectory)

        if not os.path.exists(self.loggingDirectory):
            raise ConfigError("Logging directory '%s' does not exist" % self.loggingDirectory)

        if not os.path.exists(self.modelDirectory):
            raise ConfigError("Model directory '%s' does not exist" % self.modelDirectory)


        tLoader = tornado.template.Loader(self.templateDirectory)
        self.resultsEmailBodyTemplate = tLoader.load(self.resultsEmailBodyPath)
        self.latexResultTemplate      = tLoader.load(self.latexResultTemplatePath)
        self.confirmEmailTemplate     = tLoader.load(self.confirmEmailTemplatePath)
        self.failureEmailTemplate     = tLoader.load(self.failureEmailTemplatePath)

        self.loadEmail(config)
        self.checkIntegrity()

    def loadEmail(self, config):
        self.smtpUsername = config.get("email", "smtpUsername")
        self.smtpPassword = config.get("email", "smtpPassword")
        self.smtpServer   = config.get("email", "smtpServer")
        self.smtpPort     = config.getint("email", "smtpPort")
        self.smtpUseTLS   = config.getboolean("email", "smtpUseTLS")
        self.fromAddress  = config.get("email", "fromAddress")


    def checkIntegrity(self):
        if self.matlabRequired and not os.path.exists(self.matlabPath):
            raise ConfigError("Matlab executable does not exist at '%s'" % self.matlabPath)

        if not os.path.exists(self.pdfLatexPath):
            raise ConfigError("pdflatex executable does not exist at '%s'" % self.pdfLatexPath)
        

config = Config()
