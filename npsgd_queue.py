import os
import sys
import logging

class NPSGDQueue(object):
    def __init__(self):
        self.requests = []

    def putTask(self, request):
        self.requests.append(request)
        logging.info("Added task to model queue as number %d", len(self.requests))

    def getNextTask(self):
        return self.requests.pop(0)

    def isEmpty(self):
        return len(self.requests) == 0
