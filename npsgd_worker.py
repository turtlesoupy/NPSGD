import os
import sys
import time
import json
import logging
import urllib2

import npsgd_config
import npsgd_model_manager
from npsgd_model_task import NPSGDModelTask

modelManager = npsgd_model_manager.modelManager


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
    logging.basicConfig(level=logging.DEBUG)
    npsgd_model_manager.setupModels()

    config = npsgd_config.readDefaultConfig()

    worker = NPSGDWorker(config.serverAddress, config.serverWorkerPort)
    worker.loop()


if __name__ == "__main__":
    main()
