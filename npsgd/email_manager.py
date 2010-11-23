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
        self.queue = Queue.Queue()

    def addEmail(self, email):
        self.queue.put(email)

    def run(self):
        while True:
            email = self.queue.get(True)
            logging.info("Found email in the queue, attempting to send")
            s = self.smtpServer()
            try:
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
    def __init__(self, recipient, subject, body, binaryAttachments=[]):
        self.recipient         = recipient
        self.subject           = subject
        self.body              = body
        self.binaryAttachments = binaryAttachments

    def sendThrough(self, smtpServer):
        msg = MIMEMultipart()
        msg['Subject'] = self.subject
        msg['From']    = config.fromAddress
        msg['To']      = self.recipient 

        msg.attach(MIMEText(self.body, 'plain', 'UTF-8'))

        for (name, attach) in self.binaryAttachments:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(attach)
            Encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            msg.attach(part)

        smtpServer.sendmail(config.fromAddress, [self.recipient] + config.cc, msg.as_string())

email_manager_thread = EmailManager()
email_manager_thread.start()
