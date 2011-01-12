"""Module used within the queue daemon for keeping track of confirmation codes."""
import random
import string
import logging
import threading
from datetime import datetime
from config import config

class ConfirmationEntry(object):
    def __init__(self, request):
        self.timestamp  = datetime.now()
        self.expiryTime = datetime.now() + config.confirmTimeout
        self.request    = request

    def expired(self):
        return datetime.now() >= self.expiryTime

class ExistingCodeError(RuntimeError): pass
class ConfirmationMap(object):
    """Confirmation code map (thread safe). 

    Essentially this is a wrapped hash from code string -> request with some
    helper methods to expire old confirmation entries.
    """
    def __init__(self):
        self.codeToRequest = {}
        self.codeLength    = 16
        self.lock          = threading.RLock()

    def getRequestsWithCodes(self):
        return [(code,c.request) for code,c in self.codeToRequest.iteritems()]

    def putRequestWithCode(self, request, code):
        with self.lock:
            if code in self.codeToRequest:
                raise ExistingCodeError("%s already exists in map", code)

            self.codeToRequest[code] = ConfirmationEntry(request)
    
    def putRequest(self, request):
        code = self.generateCode()
        with self.lock:
            self.codeToRequest[code] = ConfirmationEntry(request)

        return code

    def getRequest(self, code):
        with self.lock:
            if code in self.codeToRequest:
                request = self.codeToRequest[code].request
                del self.codeToRequest[code]
                return request
            else:
                raise KeyError("Code does not exist")

    def expireConfirmations(self):
        """Expire old confirmations - meant to be called at a regular rate."""

        with self.lock:
            delKeys = [k for (k,v) in self.codeToRequest.iteritems() if v.expired()]
            if len(delKeys) > 0:
                logging.info("Expiring %d confirmations" % (len(delKeys)))
                for k in delKeys:
                    del self.codeToRequest[k]

    def generateCode(self):
        return "".join(random.choice(string.letters + string.digits)\
                for i in xrange(self.codeLength))
