import random
import string
import logging
from datetime import datetime

from config import config

class ConfirmationMap(object):
    class ConfirmationEntry(object):
        def __init__(self, request):
            self.timestamp  = datetime.now()
            self.expiryTime = datetime.now() + config.confirmTimeout
            self.request    = request

        def expired(self):
            return datetime.now() >= self.expiryTime


    def __init__(self):
        self.codeToRequest = {}
        self.codeLength = 16

    def putRequest(self, request):
        code = self.generateCode()
        self.codeToRequest[code] = self.ConfirmationEntry(request)
        return code

    def getRequest(self, code):
        if code in self.codeToRequest:
            request = self.codeToRequest[code].request
            del self.codeToRequest[code]
            return request
        else:
            raise KeyError("Code does not exist")

    def expireConfirmations(self):
        delKeys = [k for (k,v) in self.codeToRequest.iteritems() if v.expired()]
        if len(delKeys) > 0:
            logging.info("Expiring %d confirmations" % (len(delKeys)))
            for k in delKeys:
                del self.codeToRequest[k]

    def generateCode(self):
        return "".join(random.choice(string.letters + string.digits)\
                for i in xrange(self.codeLength))
