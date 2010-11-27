import random
import string

class ConfirmationMap(object):
    class ConfirmationEntry(object):
        def __init__(self, request):
            self.timestamp = 10
            self.request   = request

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

    def generateCode(self):
        return "".join(random.choice(string.letters + string.digits)\
                for i in xrange(self.codeLength))
