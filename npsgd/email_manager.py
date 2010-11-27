import smtplib
import Queue
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.Utils import formatdate
from email import Encoders
from threading import Thread
import logging

from config import config

class EmailManager(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.queue = Queue.Queue()

    def addEmail(self, email):
        self.queue.put(email)

    def run(self):
        while True:
            email = self.queue.get(True)
            logging.info("Email Manager: Found email in the queue, attempting to send")
            s = self.smtpServer()
            try:
                logging.info("Email Manager: Connected to SMTP server")
                email.sendThrough(s)
            finally:
                s.close()

    def smtpServer(self):
        smtpserver = smtplib.SMTP(config.smtpServer, config.smtpPort)
        smtpserver.ehlo()
        if config.smtpUseTLS:
            smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(config.smtpUsername, config.smtpPassword)

        return smtpserver

class Email(object):
    def __init__(self, recipient, subject, body, binaryAttachments=[], textAttachments=[]):
        self.recipient         = recipient
        self.subject           = subject
        self.body              = body
        self.binaryAttachments = binaryAttachments
        self.textAttachments   = textAttachments

    def sendThrough(self, smtpServer):
        msg = MIMEMultipart()
        msg['Subject'] = self.subject
        msg['From']    = config.fromAddress
        msg['To']      = self.recipient 

        msg.attach(MIMEText(self.body, 'plain', 'UTF-8'))

        for (name, attach) in self.textAttachments:
            part = MIMEText(attach, 'plain', 'UTF-8')
            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            msg.attach(part)

        for (name, attach) in self.binaryAttachments:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(attach)
            Encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            msg.attach(part)

        logging.info("Email Thread: constructed email object, sending")
        smtpServer.sendmail(config.fromAddress, [self.recipient] + config.cc, msg.as_string())
        logging.info("Email Thread: sent")

email_manager_thread = EmailManager()
email_manager_thread.start()
