#!/usr/bin/python
"""Queue server for npsgd modelling tasks.

The queue server is the data backend for NPSGD. It listens to both workers and
the web interface. The web interface populates it with requests while the workers
poll for requests and pull them off the queue. Additionally, the queue is 
responsible for sending out confirmation code e-mail messages.
"""
import os
import sys
import anydbm
import shelve
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

glb = None
"""Queue globals object - assigned at startup."""

class QueueGlobals(object):
    """Queue state objects along with disk serialization mechanisms for them."""

    def __init__(self, shelve):
        self.shelve          = shelve
        self.shelveLock      = threading.RLock() 
        self.idLock          = threading.RLock()
        self.taskQueue       = TaskQueue()
        self.confirmationMap = ConfirmationMap()
        if shelve.has_key("idCounter"):
            self.idCounter = shelve["idCounter"]
        else:
            self.idCounter = 0

        self.loadDiskTaskQueue()
        self.loadConfirmationMap()
        self.expireWorkerTaskThread = ExpireWorkerTaskThread(self.taskQueue)
        self.lastWorkerCheckin = datetime(1,1,1)

    def loadDiskTaskQueue(self):
        """Load task queue from disk using the shelve reserved for the queue."""

        if not self.shelve.has_key("taskQueue"):
            logging.info("Unable to read task queue from disk db, starting fresh")
            return

        logging.info("Reading task queue from disk")
        readTasks   = 0
        failedTasks = 0
        taskDicts = self.shelve["taskQueue"]
        for taskDict in taskDicts:
            try:
                task = modelManager.getModelFromTaskDict(taskDict)
            except model_manager.InvalidModelError, e:
                emailAddress = taskDict["emailAddress"]
                subject = config.lostTaskEmailSubject.generate(full_name=taskDict["modelFullName"], 
                        visibleId=taskDict["visibleId"])
                body = config.lostTaskEmailTemplate.generate()
                emailObject = Email(emailAddress, subject, body)
                logging.info("Invalid model-version pair, notifying %s", emailAddress)
                npsgd.email_manager.backgroundEmailSend(Email(emailAddress, subject, body))
                failedTasks += 1
                continue
            
            readTasks += 1
            self.taskQueue.putTask(task)

        logging.info("Read %s tasks, failed while reading %s tasks", readTasks, failedTasks)

    def loadConfirmationMap(self):
        """Load confirmation map ([code, modelDict] pairs) from shelve reserved for the queue."""

        if not self.shelve.has_key("confirmationMap"):
            logging.info("Unable to read confirmation map from disk db, starting fresh")
            return

        logging.info("Reading confirmation map from disk")
        confirmationMapEntries = self.shelve["confirmationMap"]

        readCodes = 0
        failedCodes = 0
        for code, taskDict in confirmationMapEntries.iteritems():
            try:
                task = modelManager.getModelFromTaskDict(taskDict)
            except model_manager.InvalidModelError, e:
                emailAddress = taskDict["emailAddress"]
                subject = config.confirmationFailedEmailSubject.generate(full_name=taskDict["modelFullName"], 
                        visibleId=taskDict["visibleId"])
                body = config.confirmationFailedEmailTemplate.generate(code=code)
                emailObject = Email(emailAddress, subject, body)
                logging.info("Invalid model-version pair, notifying %s", emailAddress)
                npsgd.email_manager.backgroundEmailSend(Email(emailAddress, subject, body))
                failedCodes += 1
                continue

            readCodes += 1
            self.confirmationMap.putRequestWithCode(task, code)

        logging.info("Read %s codes, failed while reading %s codes", readCodes, failedCodes)


    def syncShelve(self):
        """Serializes the task queue, confirmation map and id counter to disk using the queue shelve."""
        try:
            with self.shelveLock:
                self.shelve["taskQueue"]        = [e.asDict() \
                        for e in self.taskQueue.allRequests()]
                self.shelve["confirmationMap"]  = dict( (code, task.asDict())\
                        for (code, task) in self.confirmationMap.getRequestsWithCodes())

                with self.idLock:
                    self.shelve["idCounter"] = self.idCounter
        except pickle.PicklingError, e:
            logging.warning("Unable sync task queue and confirmation error to disk due to a pickling (serialization error): %s", e)
            return

        logging.info("Synced queue and confirmation map to disk")

    def touchWorkerCheckin(self):
        self.lastWorkerCheckin = datetime.now()

    def newTaskId(self):
        with self.idLock:
            self.idCounter += 1
            return self.idCounter

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

class QueueRequestHandler(tornado.web.RequestHandler):
    """Superclass to all queue request methods."""
    def checkSecret(self):
        """Checks the request for a 'secret' parameter that matches the queue's own."""
        if self.get_argument("secret") == config.requestSecret:
            return True
        else:
            self.write(tornado.escape.json_encode({"error": "bad_secret"}))
            return False

class ClientModelCreate(QueueRequestHandler):
    """HTTP handler for clients creating a model request (before confirmation)."""

    def post(self):
        """Post handler for model requests from the web daemon.

        Attempts to build a model from its known models (essentially performing
        parameter verification) then places a request in the queue if it succeeds.
        Additionally, it will send out an e-mail to the user for confirmation of
        the request
        """

        if not self.checkSecret():
            return

        task_json = tornado.escape.json_decode(self.get_argument("task_json"))
        task = modelManager.getModelFromTaskDict(task_json)
        task.taskId = glb.newTaskId()
        code = glb.confirmationMap.putRequest(task)

        emailAddress = task.emailAddress
        logging.info("Generated a request for %s, confirmation %s required", emailAddress, code)
        subject = config.confirmEmailSubject.generate(task=task)
        body = config.confirmEmailTemplate.generate(code=code, task=task, expireDelta=config.confirmTimeout)
        emailObject = Email(emailAddress, subject, body)
        npsgd.email_manager.backgroundEmailSend(emailObject)
        glb.syncShelve()
        self.write(tornado.escape.json_encode({
            "response": {
                "task" : task.asDict(),
                "code" : code
            }    
        }))

class ClientQueueHasWorkers(QueueRequestHandler):
    """Request handler for the web daemon to check if workers are available.

    We keep track of the last time workers checked into the queue in order
    to ensure that all requests can be processed.
    """

    def get(self):
        if not self.checkSecret():
            return

        td = datetime.now() - glb.lastWorkerCheckin
        hasWorkers = (td.seconds + td.days * 24 * 3600) < config.keepAliveTimeout

        self.write(tornado.escape.json_encode({
            "response": {
                "has_workers" : hasWorkers
            }    
        }))


previouslyConfirmed = set()
class ClientConfirm(QueueRequestHandler):
    """HTTP handler for clients confirming a model request.
    
    This handler moves requests from the confirmation map to the general
    request queue for processing.
    """
    def get(self, code):
        global previouslyConfirmed

        if not self.checkSecret():
            return

        try:
            #Expire old confirmations first, just in case
            glb.confirmationMap.expireConfirmations()
            confirmedRequest = glb.confirmationMap.getRequest(code)
            previouslyConfirmed.add(code)
        except KeyError, e:
            if code in previouslyConfirmed:
                self.write(tornado.escape.json_encode({
                    "response": "already_confirmed"
                }))
                return
            else:
                raise tornado.web.HTTPError(404)

        glb.taskQueue.putTask(confirmedRequest)
        glb.syncShelve()
        self.write(tornado.escape.json_encode({
            "response": "okay"
        }))


class WorkerInfo(QueueRequestHandler):
    """HTTP handler for workers checking into the queue."""

    def get(self):
        if not self.checkSecret():
            return

        glb.touchWorkerCheckin()
        self.write("{}")

class WorkerTaskKeepAlive(QueueRequestHandler):
    """HTTP handler for workers pinging the queue while working on a task.
    
    Having this request makes sure that we don't time out any jobs that 
    are currently being handled by some worker. If a worker goes down,
    we will put the job back into the queue because this request won't have
    been made.
    """
    def get(self, taskIdString):
        if not self.checkSecret():
            return
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

class WorkerSucceededTask(QueueRequestHandler):
    """HTTP handler for workers telling the queue that they have succeeded processing.

    After this request, the queue no longer needs to keep track of the job in any way
    and declares it complete.
    """

    def get(self, taskIdString):
        if not self.checkSecret():
            return
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

        glb.syncShelve()
        self.write(tornado.escape.json_encode({
            "status": "okay"
        }))

class WorkerHasTask(QueueRequestHandler):
    """HTTP handler for workers ensuring that a job still exists.

    This handler helps eliminate certain race conditions in NPSGD. Before a 
    worker sends an e-mail with job results, it checks back with the queue to
    make sure that the job hasn't already been handler by another worker
    (this could happen if the queue declares that the first worker had timed out).
    If there is no task with that id still in the processing list then 
    an e-mail being sent out would be a duplicate.
    """

    def get(self, taskIdString):
        if not self.checkSecret():
            return

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

class WorkerFailedTask(QueueRequestHandler):
    """HTTP handler for workers reporting failure to complete a job.
    
    Upon failure, we will either recycle the request into the queue or we will
    report a failure (with an e-mail message to the user).
    """

    def get(self, taskIdString):
        if not self.checkSecret():
            return

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


class WorkerTaskRequest(QueueRequestHandler):
    """HTTP handler for workers grabbings tasks off the queue."""
    def post(self):
        if not self.checkSecret():
            return

        modelVersions = tornado.escape.json_decode(self.get_argument("model_versions_json"))

        glb.touchWorkerCheckin()
        logging.info("Received worker task request with models %s", modelVersions)
        if glb.taskQueue.isEmpty():
            self.write(tornado.escape.json_encode({
                "status": "empty_queue"
            }))
        else:
            task = glb.taskQueue.pullNextVersioned(modelVersions)
            if task == None:
                logging.info("Found no models in queue matching worker's supported versions")
                self.write(tornado.escape.json_encode({
                    "status": "no_version"
                }))
            else:
                glb.taskQueue.putProcessingTask(task)
                self.write(tornado.escape.json_encode({
                    "task": task.asDict()
                }))

def main():
    global glb
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

    try:
        queueShelve  = shelve.open(config.queueFile)
    except anydbm.error:
        logging.warning("Queue file '%s' is corrupt, removing and starting afresh", config.queueFile)
        os.remove(config.queueFile)
        queueShelve = shelve.open(config.queueFile)

    try:
        glb = QueueGlobals(queueShelve)
        queueHTTP = tornado.httpserver.HTTPServer(tornado.web.Application([
            (r"/worker_info", WorkerInfo),
            (r"/client_model_create", ClientModelCreate),
            (r"/client_queue_has_workers", ClientQueueHasWorkers),
            (r"/client_confirm/(\w+)", ClientConfirm),
            (r"/worker_failed_task/(\d+)", WorkerFailedTask),
            (r"/worker_succeed_task/(\d+)", WorkerSucceededTask),
            (r"/worker_has_task/(\d+)",     WorkerHasTask),
            (r"/worker_keep_alive_task/(\d+)", WorkerTaskKeepAlive),
            (r"/worker_work_task", WorkerTaskRequest)
        ]))
        queueHTTP.listen(options.port)
        logging.info("NPSGD Queue Booted up, serving on port %d", options.port)
        print >>sys.stderr, "NPSGD queue server listening on %d" % options.port
        tornado.ioloop.IOLoop.instance().start()
    finally:
        queueShelve.close()


if __name__ == "__main__":
    main()
