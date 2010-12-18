#!/usr/bin/python
import os
import sys
import logging
import tornado.web
import tornado.ioloop
import tornado.escape
import tornado.httpserver
import threading
from datetime import datetime
from optparse import OptionParser

import npsgd.email_manager
from npsgd.email_manager import Email
from npsgd import model_manager
from npsgd.config import config
from npsgd.task_queue import TaskQueue
from npsgd.task_queue import TaskQueueException
from npsgd.confirmation_map import ConfirmationMap
from npsgd.model_manager import modelManager

"""Queue server for npsgd modelling tasks."""

class ExpireWorkerTaskThread(threading.Thread):
    """Task Expiration Thread

    Moves tasks back into the queue whenever
    We haven't heard from a worker in a while
    """

    def __init__(self, taskQueue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.taskQueue = taskQueue
        self.done = threading.Event()

    def run(self):
        logging.info("Expire worker task thread booting up...")

        while True:
            self.done.wait(config.keepAliveInterval)
            if self.done.isSet():
                break

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
                    task.taskId = glb.newTaskId()
                    self.taskQueue.putTask(task)

class QueueGlobals(object):
    def __init__(self):
        self.idCounter = 0
        self.idLock = threading.RLock()
        self.taskQueue = TaskQueue()
        self.confirmationMap = ConfirmationMap()
        self.expireWorkerTaskThread = ExpireWorkerTaskThread(self.taskQueue)
        self.lastWorkerCheckin = datetime(1,1,1)

    def touchWorkerCheckin(self):
        self.lastWorkerCheckin = datetime.now()

    def newTaskId(self):
        with self.idLock:
            self.idCounter += 1
            return self.idCounter

glb = QueueGlobals()

class ClientModelCreate(tornado.web.RequestHandler):
    def post(self):
        task_json = tornado.escape.json_decode(self.get_argument("task_json"))
        model = modelManager.getModel(task_json["modelName"], task_json["modelVersion"])
        task  = model.fromDict(task_json)
        task.taskId = glb.newTaskId()
        code = glb.confirmationMap.putRequest(task)

        emailAddress = task.emailAddress
        logging.info("Generated a request for %s, confirmation %s required", emailAddress, code)
        body = config.confirmEmailTemplate.generate(code=code, task=task, expireDelta=config.confirmTimeout)
        emailObject = Email(emailAddress, config.confirmEmailSubject, body)
        npsgd.email_manager.backgroundEmailSend(emailObject)
        self.write(tornado.escape.json_encode({
            "response": {
                "task" : task.asDict(),
                "code" : code
            }    
        }))

class ClientQueueHasWorkers(tornado.web.RequestHandler):
    def get(self):
        td = datetime.now() - glb.lastWorkerCheckin
        hasWorkers = (td.seconds + td.days * 24 * 3600) < config.keepAliveTimeout

        self.write(tornado.escape.json_encode({
            "response": {
                "has_workers" : hasWorkers
            }    
        }))


class ClientConfirm(tornado.web.RequestHandler):
    def get(self, code):
        try:
            #Expire old confirmations first, just in case
            glb.confirmationMap.expireConfirmations()
            confirmedRequest = glb.confirmationMap.getRequest(code)
        except KeyError, e:
            raise tornado.web.HTTPError(404)

        glb.taskQueue.putTask(confirmedRequest)
        self.write(tornado.escape.json_encode({
            "response": "okay"
        }))


class WorkerInfo(tornado.web.RequestHandler):
    def get(self):
        glb.touchWorkerCheckin()
        self.write("{}")

class WorkerTaskKeepAlive(tornado.web.RequestHandler):
    def get(self, taskIdString):
        glb.touchWorkerCheckin()
        taskId = int(taskIdString)
        logging.info("Got heartbeat for task id '%s'", taskId)
        try:
            task = glb.taskQueue.touchProcessingTaskById(taskId)
        except TaskQueueException, e:
            logging.info("Bad keep alive request: no such task id '%s' exists" % taskId)
            self.write(tornado.escape.json_encode({
                "error": {"type" : "bad_id" }
            }))

        self.write("{}")

class WorkerSucceededTask(tornado.web.RequestHandler):
    def get(self, taskIdString):
        glb.touchWorkerCheckin()
        taskId = int(taskIdString)
        try:
            task = glb.taskQueue.pullProcessingTaskById(taskId)
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
        glb.touchWorkerCheckin()
        taskId = int(taskIdString)
        logging.info("Got 'has task' request for task of id '%d'", taskId)
        if glb.taskQueue.hasProcessingTaskById(taskId):
            self.write(tornado.escape.json_encode({
                "response": "yes"
            }))
        else:
            self.write(tornado.escape.json_encode({
                "response": "no"
            }))

class WorkerFailedTask(tornado.web.RequestHandler):
    def get(self, taskIdString):
        glb.touchWorkerCheckin()
        taskId = int(taskIdString)
        try:
            task = glb.taskQueue.pullProcessingTaskById(taskId)
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
            glb.taskQueue.putTask(task)

        self.write(tornado.escape.json_encode({
            "status": "okay"
        }))


class WorkerTaskRequest(tornado.web.RequestHandler):
    def get(self):
        glb.touchWorkerCheckin()
        logging.info("Received worker task request")
        if glb.taskQueue.isEmpty():
            self.write(tornado.escape.json_encode({
                "status": "empty_queue"
            }))
        else:
            task = glb.taskQueue.pullNextTask()
            glb.taskQueue.putProcessingTask(task)
            self.write(tornado.escape.json_encode({
                "task": task.asDict()
            }))


def setupQueueApplication():
    return tornado.web.Application([
        (r"/worker_info", WorkerInfo),
        (r"/client_model_create", ClientModelCreate),
        (r"/client_queue_has_workers", ClientQueueHasWorkers),
        (r"/client_confirm/(\w+)", ClientConfirm),
        (r"/worker_failed_task/(\d+)", WorkerFailedTask),
        (r"/worker_succeed_task/(\d+)", WorkerSucceededTask),
        (r"/worker_has_task/(\d+)",     WorkerHasTask),
        (r"/worker_keep_alive_task/(\d+)", WorkerTaskKeepAlive),
        (r"/worker_work_task", WorkerTaskRequest)
    ])

def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                        help="Config file", default="config.cfg")
    parser.add_option("-p", "--port", dest="port",
                        help="Queue port number", default=9000)
    parser.add_option('-l', '--log-filename', dest='log',
                        help="Log filename (use '-' for stderr)", default="-")

    (options, args) = parser.parse_args()

    config.loadConfig(options.config)
    config.setupLogging(options.log)
    model_manager.setupModels()
    model_manager.startScannerThread()

    queueHTTP = tornado.httpserver.HTTPServer(setupQueueApplication())
    queueHTTP.listen(options.port)
    logging.info("NPSGD Queue Booted up, serving on port %d", options.port)
    print >>sys.stderr, "NPSGD queue server listening on %d" % options.port

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
