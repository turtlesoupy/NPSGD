import os
import sys
import time
import json
import logging
import urllib2
from optparse import OptionParser

from npsgd import config
from npsgd import model_manager
from npsgd.model_manager import modelManager
from npsgd.model_task import ModelTask
from npsgd.config import config

class NPSGDWorker(object):
    def __init__(self, serverAddress, serverPort):
        self.baseRequest     = "http://%s:%s" % (serverAddress, serverPort)
        self.infoRequest     = "%s/info"      % self.baseRequest
        self.taskRequest     = "%s/work_task" % self.baseRequest
        self.requestTimeout  = 100
        self.supportedModels = ["test"]
        self.requestErrors   = 0
        self.maxErrors       = 3 
        self.errorSleepTime    = 3
        self.requestSleepTime = 10
        self.getServerInfo()

    def getServerInfo(self):
        try:
            response = urllib2.urlopen(self.infoRequest)
        except urllib2.URLError, e:
            logging.error("Failed to make initial connection to %s", self.baseRequest)
            sys.exit(1)
        
        logging.info("Got initial response from server")

    def responseError(self):
        self.requestErrors += 1
        if self.requestErrors >= self.maxErrors:
            logging.critical("Exceeded max errors of %d, terminating", self.maxErrors)
            sys.exit(1)
        time.sleep(self.errorSleepTime)

    def loop(self):
        logging.info("Entering event loop")
        while True:
            try:
                logging.info("Polling %s for tasks" % self.taskRequest)
                response = urllib2.urlopen(self.taskRequest)
            except urllib2.URLError, e:
                logging.error("Error making worker request to server, attempt #%d", self.requestErrors + 1)
                self.responseError()
                continue

            try:
                decodedResponse = json.load(response)
            except ValueError, e:
                logging.error("Error decoding server response, attempt #%d", self.requestErrors +1)
                self.responseError()
                continue

            self.processResponse(decodedResponse)
            time.sleep(self.requestSleepTime)

    def processResponse(self, response):
        if "status" in response:
            if response["status"] == "empty_queue":
                logging.info("No tasks available on server")
        elif "task" in response:
            self.processTask(response["task"])

    def processTask(self, taskDict):
        try:
            model = modelManager.getModel(taskDict["modelName"])
            logging.info("Creating a model task for '%s'", taskDict["modelName"])
            taskObject = model.fromDict(taskDict)
        except KeyError, e:
            logging.warning("Was unable to deserialize model task")
            return

        taskObject.run()

def main():
    parser = OptionParser()
    parser.add_option('-a', '--server-address', dest="server_address",
            help="Server address (default 127.0.0.1)", type="string", default="127.0.0.1")
    parser.add_option('-p', '--server-port', dest="server_port",
            help="Server port (default 8001)", type="int", default="8001")
    parser.add_option('-c', '--config', dest="config",
            help="Configuration file path", type="string", default="config.cfg")

    (options, args) = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    config.loadConfig(options.config)
    model_manager.setupModels()


    worker = NPSGDWorker(options.server_address, options.server_port)
    worker.loop()

if __name__ == "__main__":
    main()
