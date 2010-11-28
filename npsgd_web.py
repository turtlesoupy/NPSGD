import os
import sys
import time
import logging
import threading
import tornado.web
import tornado.ioloop
import tornado.escape
import tornado.httpserver
from optparse import OptionParser

from npsgd.email_manager import Email
from npsgd.email_manager import email_manager_thread 
from npsgd import model_manager
from npsgd import model_parameters
from npsgd import ui_modules

from npsgd.confirmation_map import ConfirmationMap
from npsgd.model_manager import modelManager
from npsgd.task_queue import TaskQueue
from npsgd.task_queue import TaskQueueException
from npsgd.model_task import ModelTask
from npsgd.config import config


class ExpireWorkerTaskThread(threading.Thread):
    """Task Expiration Thread
    
    Moves tasks back into the queue whenever 
    We haven't heard from a worker in a while
    """

    def __init__(self, taskQueue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.taskQueue = taskQueue
        self.done = False

    def run(self):
        logging.info("Expire worker task thread booting up...")

        while not self.done:
            badTasks = self.taskQueue.pullProcessingTasksOlderThan(
                    time.time() - config.keepAliveTimeout)

            if len(badTasks) > 0:
                logging.info("Found %d tasks to expire", len(badTasks))

            for task in badTasks:
                task.failureCount += 1
                logging.warning("Task '%s' failed due to timeout (failure #%d)", task.taskId, task.failureCount)
                if task.failureCount > config.maxJobFailures:
                    logging.warning("Exceeded max job failures, sending fail email")
                    npsgd.email_manager.backgroundEmailSend(task.failureEmail())
                else:
                    logging.warning("Inserting task back in to queue with new taskId")
                    task.taskId = newTaskId()
                    self.taskQueue.putTask(task)

            time.sleep(config.keepAliveInterval)

#Some globals
idCounter    = 0
confirmationMap = ConfirmationMap()
modelQueue      = TaskQueue()
expireWorkerTaskThread = ExpireWorkerTaskThread(modelQueue)

def newTaskId():
    global idCounter
    idCounter += 1

    return idCounter

class ClientModelRequest(tornado.web.RequestHandler):
    def initialize(self, model):
        self.model = model

    def post(self):
        try:
            task = self.setupModelTask()
        except tornado.web.HTTPError, e:
            self.render(config.modelTemplatePath, model=self.model)
            return

        self.pushAndRender(task)

    def pushAndRender(self, task):
        code = confirmationMap.putRequest(task)
        emailAddress = task.emailAddress
        logging.info("Generated a request for %s, confirmation %s required", emailAddress, code)
        body = config.confirmEmailTemplate.generate(code=code)
        emailObject = Email(emailAddress, config.confirmEmailSubject, body, [], [("parameters.txt", task.textParameterTable())])
        #npsgd.email_manager.backgroundEmailSend(emailObject)
        self.render(config.confirmTemplatePath, email=emailAddress, code=code)

    def setupModelTask(self):
        email = self.get_argument("email")

        paramDict = {}
        for param in self.model.parameters:
            argVal = self.get_argument(param.name)
            value = param.withValue(argVal)
            paramDict[param.name] = value.asDict()

        task = self.model(email, newTaskId(), paramDict)
        return task


class ClientBaseRequest(tornado.web.RequestHandler):
    def get(self):
        self.write("Find a model!")

class ClientConfirmRequest(tornado.web.RequestHandler):
    def get(self, confirmationCode):
        try:
            confirmedRequest = confirmationMap.getRequest(confirmationCode)
        except KeyError, e:
            raise tornado.web.HTTPError(404)

        logging.info("Client confirmed request %s", confirmationCode)
        modelQueue.putTask(confirmedRequest)

        self.render(config.confirmedTemplatePath)
            

class WorkerInfo(tornado.web.RequestHandler):
    def get(self):
        self.write("{}")

class WorkerTaskKeepAlive(tornado.web.RequestHandler):
    def get(self, taskIdString):
        taskId = int(taskIdString)
        logging.info("Got heartbeat for task id '%s'", taskId)
        try:
            task = modelQueue.touchProcessingTaskById(taskId)
        except TaskQueueException, e:
            logging.info("Bad keep alive request: no such task id '%s' exists" % taskId)
            self.write(tornado.escape.json_encode({
                "error": {"type" : "bad_id" }
            }))

        self.write("{}")

class WorkerSucceededTask(tornado.web.RequestHandler):
    def get(self, taskIdString):
        taskId = int(taskIdString)
        try:
            task = modelQueue.pullProcessingTaskById(taskId)
        except TaskQueueException, e:
            logging.info("Bad succeed request: no task id exists")
            self.write(tornado.escape.json_encode({
                "error": {"type" : "bad_id" }
            }))
            return

        self.write(tornado.escape.json_encode({
            "status": "okay"
        }))

class WorkerHasTask(tornado.web.RequestHandler):
    def get(self, taskIdString):
        taskId = int(taskIdString)
        logging.info("Got 'has task' request for task of id '%d'", taskId)
        if modelQueue.hasProcessingTaskById(taskId):
            self.write(tornado.escape.json_encode({
                "response": "yes"
            }))
        else:
            self.write(tornado.escape.json_encode({
                "response": "no"
            }))

class WorkerFailedTask(tornado.web.RequestHandler):
    def get(self, taskIdString):
        taskId = int(taskIdString)
        try:
            task = modelQueue.pullProcessingTaskById(taskId)
        except TaskQueueException, e:
            logging.info("Bad failed request: no such task id exists, ignoring request")
            self.write(tornado.escape.json_encode({
                "error": {"type" : "bad_id" }
            }))
            return

        task.failureCount += 1
        logging.warning("Worker had a failure while processing task '%s' (failure #%d)",\
                task.taskId, task.failureCount)

        if task.failureCount >= config.maxJobFailures:
            logging.warning("Max job failures found, sending failure email")
            npsgd.email_manager.backgroundEmailSend(task.failureEmail())
        else:
            logging.warning("Returning task to queue for another attempt")
            modelQueue.putTask(task)

        self.write(tornado.escape.json_encode({
            "status": "okay"
        }))
        
class WorkerTaskRequest(tornado.web.RequestHandler):
    def get(self):
        logging.info("Received worker task request")
        if modelQueue.isEmpty():
            self.write(tornado.escape.json_encode({
                "status": "empty_queue"
            }))
        else:
            task = modelQueue.pullNextTask()
            modelQueue.putProcessingTask(task)
            self.write(tornado.escape.json_encode({
                "task": task.asDict()
            }))


def setupClientApplication():
    appList = [ 
        (r"/", ClientBaseRequest),
        (r"/confirm_submission/(\w+)", ClientConfirmRequest)
    ]

    for modelName in modelManager.modelNames():
        appList.append(("/models/%s" % modelName, ClientModelRequest, dict(model=modelManager.getModel(modelName))))

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "ui_modules": ui_modules
    }

    return tornado.web.Application(appList, **settings)

def setupWorkerApplication():
    return tornado.web.Application([
        (r"/info", WorkerInfo),
        (r"/failed_task/(\d+)", WorkerFailedTask),
        (r"/succeed_task/(\d+)", WorkerSucceededTask),
        (r"/has_task/(\d+)",     WorkerHasTask),
        (r"/keep_alive_task/(\d+)", WorkerTaskKeepAlive),
        (r"/work_task", WorkerTaskRequest)
    ])

def main():
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config',
                        help="Config file", default="config.cfg")
    parser.add_option('-p', '--client-port', dest='client_port',
                        help="Client http port (for serving html)", default=8000, type="int")
    parser.add_option('-w', '--worker-port', dest='worker_port',
                        help="Worker port (for serving html)", default=8001, type="int")

    (options, args) = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    config.loadConfig(options.config)
    model_manager.setupModels()
    clientHTTP = tornado.httpserver.HTTPServer(setupClientApplication())
    workerHTTP = tornado.httpserver.HTTPServer(setupWorkerApplication())

    clientHTTP.listen(options.client_port)
    workerHTTP.listen(options.worker_port)

    print >>sys.stderr, "NPSGD web server running on port %d" % options.client_port
    print >>sys.stderr, "NPSGD worker server running on port %d" % options.worker_port

    expireWorkerTaskThread.start()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
