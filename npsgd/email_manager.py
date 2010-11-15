import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.Utils import formatdate
from email import Encoders

username = 'npsg@thomasdimson.com'
password = 'b00boo'

def setupSMTP():
    smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(username, password)
    return smtpserver


def sendMessage(sendTo, subject, body, binaryAttachments=[]):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = username
    msg['To'] = sendTo
    msg.attach(MIMEText(body, 'plain', 'UTF-8'))

    for (name, attach) in binaryAttachments:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attach)
        Encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=%s" % name)
        msg.attach(part)

    s = setupSMTP()
    s.sendmail(username, [sendTo], msg.as_string())
    s.close()
