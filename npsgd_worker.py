import os
import sys
import logging
import urllib2

import npsgd_config


class NPSGDWorker(object):
    def __init__(self, serverAddress, serverPort):
        self.baseRequest     = "http://%s:%s" % (serverAddress, serverPort)
        self.taskRequest     = "%s/work_task" % self.baseRequest
        self.requestTimeout  = 100
        self.supportedModels = ["test"]
        self.requestErrors   = 0
        self.maxErrors       = 3 
        self.getServerInfo()

    def getServerInfo(self):
        try:
            response = urllib2.urlopen(self.baseRequest)
        except urllib2.URLError, e:
            logging.error("Failed to make initial connection to %s", self.baseRequest)
            sys.exit(1)
        
        logging.info("Got initial response from server")

    def loop(self):
        logging.info("Entering event loop")
        while True:
            try:
                response = urllib2.urlopen(self.taskRequest)
            except urllib2.URLError, e:
                logging.error("Error making worker request to server")
                self.requestErrors += 1
                if self.requestErrors >= self.maxErrors:
                    logging.critical("Exceeded max errors of %d, terminating", self.maxErrors)



def main():
    logging.basicConfig(level=logging.DEBUG)
    config = npsgd_config.readDefaultConfig()

    worker = NPSGDWorker(config.serverAddress, config.serverPort)
    worker.loop()




if __name__ == "__main__":
    main()
