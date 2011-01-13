# Author: Thomas Dimson [tdimson@gmail.com]
# Date:   January 2011
# For distribution details, see LICENSE
"""NPSGD e-mail related module for blocking/non-blocking sends."""
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
    """Attempt to send an e-mail synchronously, reporting an error if we fail."""
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
    """Attempt to send an e-mail asynchronously, spawning a background thread if necesarry.

    This method sends an e-mail in the background using an e-mail thread. Note that
    this has a side effect of actually spawning an e-mail thread if none exists already.
    """

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
    """Thread for sending e-mail in the background (using a queue of e-mails)."""

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.queue = Queue.Queue()

    def addEmail(self, email):
        self.queue.put(email)

    def run(self):
        """Blocks on the queue until it has an e-mail in it, then send it."""
        while True:
            try:
                email = self.queue.get(True)
                logging.info("Email Manager: Found email in the queue, attempting to send")
                blockingEmailSend(email)
            except Exception:
                logging.exception("Unhandled exception in email thread!")
                self.queue.put(email)

class Email(object):
    """Actual e-mail object containing all information needed to send an e-mail.

    The e-mail object includes the recipient, subject, body, attachments and
    also contains a method to send through a given smtp server."""

    def __init__(self, recipient, subject, body, binaryAttachments=[], textAttachments=[]):
        self.recipient         = recipient
        self.subject           = subject
        self.body              = body
        self.binaryAttachments = binaryAttachments
        self.textAttachments   = textAttachments

    def sendThrough(self, smtpServer):
        """Sends this e-mail through a given smtp server (blocking)."""
        msg = MIMEMultipart()
        #headers
        msg['To']      = self.recipient 
        if len(config.cc) > 0:
            msg['Cc'] = ",".join(config.cc)
        msg['From']    = config.fromAddress
        msg['Subject'] = self.subject

        #actual recipients
        recipients = [self.recipient] + config.cc + config.bcc

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

        logging.info("Email: constructed email object, sending to %s", ", ".join(recipients))
        smtpServer.sendmail(config.fromAddress, recipients, msg.as_string())
        logging.info("Email: sent")

