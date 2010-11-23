import os
import sys
import random
import string
import logging
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

from npsgd.model_manager import modelManager
from npsgd.task_queue import TaskQueue
from npsgd.model_task import ModelTask
from npsgd.config import config

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
        emailObject = Email(emailAddress, config.confirmEmailSubject, body)
        email_manager_thread.addEmail(emailObject)
        self.render(config.confirmTemplatePath, email=emailAddress, code=code)

    def setupModelTask(self):
        email = self.get_argument("email")

        paramDict = {}
        for param in self.model.parameters:
            argVal = self.get_argument(param.name)
            value = param.withValue(argVal)
            paramDict[param.name] = value.asDict()

        task = self.model(email, paramDict)
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

class WorkerTaskRequest(tornado.web.RequestHandler):
    #TODO: make this async, wake up on queue fill
    def get(self):
        logging.info("Received worker task request")
        if modelQueue.isEmpty():
            self.write(tornado.escape.json_encode({
                "status": "empty_queue"
            }))
        else:
            task = modelQueue.getNextTask()
            self.write(tornado.escape.json_encode({
                "task": task.asDict()
            }))

modelQueue      = TaskQueue()
confirmationMap = ConfirmationMap()

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

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
