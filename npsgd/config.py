import os
import sys
import logging
import ConfigParser
import tornado.template


class ConfigError(RuntimeError): pass
class Config(object):
    def __init__(self):
        pass

    def loadConfig(self, configPath):
        config = ConfigParser.SafeConfigParser()
        config.read(configPath)

        self.matlabPath     = config.get('Matlab', 'matlabPath')
        self.matlabRequired = config.getboolean('Matlab', 'required')
        self.pdfLatexPath   = config.get('Latex',  'pdfLatexPath')
        self.resultsEmailBodyPath     = config.get("npsgd", "resultsEmailBodyPath")
        self.confirmEmailTemplatePath = config.get("npsgd", "confirmEmailTemplatePath")
        self.confirmEmailSubject      = config.get("npsgd", "confirmEmailSubject")
        self.latexResultTemplatePath  = config.get('Latex', 'resultTemplate')
        self.modelTemplatePath        = config.get('npsgd', 'modelTemplatePath')
        self.confirmTemplatePath      = config.get('npsgd', 'confirmTemplatePath')
        self.confirmedTemplatePath    = config.get('npsgd', 'confirmedTemplatePath')

        if not os.path.exists(self.resultsEmailBodyPath):
            raise ConfigError("Results email body does not exist")

        if not os.path.exists(self.latexResultTemplatePath):
            raise ConfigError("Latex result template file does not exist")

        if not os.path.exists(self.confirmEmailTemplatePath):
            raise ConfigError("Confirm email template '%s' is missing" % self.confirmEmailTemplatePath)

        if not os.path.exists(self.modelTemplatePath):
            raise ConfigError("Model template '%s' is missing" % self.modelTemplatePath)

        if not os.path.exists(self.confirmTemplatePath):
            raise ConfigError("Confirm template '%s' is missing" % self.confirmTemplatePath)

        if not os.path.exists(self.confirmedTemplatePath):
            raise ConfigError("Confirmed template '%s' is missing" % self.confirmedTemplatePath)

        with open(self.resultsEmailBodyPath, 'r') as f:
            self.resultsEmailBodyTemplate = tornado.template.Template(f.read())

        with open(self.latexResultTemplatePath, 'r') as f:
            self.latexResultTemplate = tornado.template.Template(f.read())

        with open(self.confirmEmailTemplatePath, 'r') as f:
            self.confirmEmailTemplate = tornado.template.Template(f.read())

        self.loadEmail(config)
        self.checkIntegrity()

    def loadEmail(self, config):
        self.smtpUsername = config.get("email", "smtpUsername")
        self.smtpPassword = config.get("email", "smtpPassword")
        self.smtpServer   = config.get("email", "smtpServer")
        self.smtpPort     = config.getint("email", "smtpPort")
        self.smtpUseTLS   = config.getboolean("email", "smtpUseTLS")
        self.fromAddress  = config.get("email", "fromAddress")
        self.cc           = config.get("email", "cc").split(",")


    def checkIntegrity(self):
        if self.matlabRequired and not os.path.exists(self.matlabPath):
            raise ConfigError("Matlab executable does not exist at '%s'" % self.matlabPath)

        if not os.path.exists(self.pdfLatexPath):
            raise ConfigError("pdflatex executable does not exist at '%s'" % self.pdfLatexPath)
        

config = Config()
