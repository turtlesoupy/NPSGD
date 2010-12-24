import smtplib
import Queue
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.Utils import formatdate
from email import Encoders
from threading import Thread
import mimetypes
import logging
import socket

from config import config

class EmailSendError(RuntimeError): pass


def blockingEmailSend(email):
    try:
        s = smtpServer()
    except socket.gaierror, e:
        raise EmailSendError("Unable to connect to smtp server")
    

    try:
        logging.info("Connected to SMTP server, sending email")
        email.sendThrough(s)
    finally:
        s.close()

email_manager_thread = None
def backgroundEmailSend(email):
    global email_manager_thread
    if email_manager_thread == None:
        email_manager_thread = EmailManagerThread()
        email_manager_thread.start()

    email_manager_thread.addEmail(email)

def smtpServer():
    smtpserver = smtplib.SMTP(config.smtpServer, config.smtpPort)
    smtpserver.ehlo()
    if config.smtpUseTLS:
        smtpserver.starttls()
    if config.smtpUseAuth:
        smtpserver.ehlo()
        smtpserver.login(config.smtpUsername, config.smtpPassword)

    return smtpserver

class EmailManagerThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.queue = Queue.Queue()

    def addEmail(self, email):
        self.queue.put(email)

    def run(self):
        while True:
            try:
                email = self.queue.get(True)
                logging.info("Email Manager: Found email in the queue, attempting to send")
                blockingEmailSend(email)
            except Exception:
                logging.exception("Unhandled exception in email thread!")
                self.queue.put(email)

class Email(object):
    def __init__(self, recipient, subject, body, binaryAttachments=[], textAttachments=[]):
        self.recipient         = recipient
        self.subject           = subject
        self.body              = body
        self.binaryAttachments = binaryAttachments
        self.textAttachments   = textAttachments

    def sendThrough(self, smtpServer):
        msg = MIMEMultipart()
        #headers
        msg['Subject'] = self.subject
        msg['From']    = config.fromAddress
        msg['To']      = self.recipient 

        #actual recipients
        recipients = [self.recipient] + config.bcc

        msg.attach(MIMEText(self.body))

        for (name, attach) in self.textAttachments:
            part = MIMEText(attach, 'plain', 'UTF-8')
            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            msg.attach(part)

        for (name, attach) in self.binaryAttachments:
            ctype, encoding = mimetypes.guess_type(name)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'

            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                part = MIMEText(attach,  _subtype=subtype)
            elif maintype == 'image':
                part = MIMEImage(attach, _subtype=subtype)
            elif maintype == 'audio':
                part = MIMEAudio(attach, _subtype=subtype)
            else:
                part = MIMEBase(maintype, subtype)
                part.set_payload(attach)
                Encoders.encode_base64(part)

            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            msg.attach(part)

        logging.info("Email: constructed email object, sending")
        smtpServer.sendmail(config.fromAddress, recipients, msg.as_string())
        logging.info("Email: sent")

