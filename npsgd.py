import os
import sys
import random
import string
import logging
import tornado.web
import tornado.ioloop
import tornado.escape
import tornado.httpserver

import npsgd_email
import npsgd_model_manager
from npsgd_model_manager import modelManager
from npsgd_queue import NPSGDQueue
from npsgd_model_task import NPSGDModelTask
import npsgd_model_parameters
import npsgd_ui_modules

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

    def get(self):
        self.render('model.html', model=self.model)

    def post(self):
        task = self.setupModelTask()
        code = confirmationMap.putRequest(task)
        email = task.emailAddress
        logging.info("Generated a request for %s, confirmation %s required", email, code)
        msg="""
Hi,

Someone from this email address recently submitted a message using the NPSG online
model tool. We need confirmation in order for you to proceed:

Visit http://192.168.245.110:8000/confirm_submission/%s to start your job.

Natural Phenomenon Simulation Group
University of Waterloo
""" % (code,)
        npsgd_email.sendMessage(email, "NPSG Model Run (Confirmation Required)", msg)
        self.render("confirm.html", email=email, code=code)



    def setupModelTask(self):
        email = self.get_argument("email")
        task  = NPSGDModelTask(email)
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

        self.write("Successful confirmation!")
        logging.info("Client confirmed request %s", confirmationCode)
        modelQueue.putTask(confirmedRequest)
            

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

modelQueue = NPSGDQueue()
confirmationMap = ConfirmationMap()



def setupClientApplication():
    appList = [ 
        (r"/", ClientBaseRequest),
        (r"/confirm_submission/(\w+)", ClientConfirmRequest)
    ]

    for modelName in modelManager.modelNames():
        appList.append(("/models/%s" % modelName, ClientModelRequest, dict(model=modelManager.getModel(modelName))))

    settings = {
        "ui_modules": npsgd_ui_modules
    }

    return tornado.web.Application(appList, **settings)

def setupWorkerApplication():
    return tornado.web.Application([
        (r"/info", WorkerInfo),
        (r"/work_task", WorkerTaskRequest)
    ])


clientPort = 8000
workerPort = 8001

def main():
    logging.basicConfig(level=logging.DEBUG)
    npsgd_model_manager.setupModels()
    port = 8000
    clientHTTP = tornado.httpserver.HTTPServer(setupClientApplication())
    workerHTTP = tornado.httpserver.HTTPServer(setupWorkerApplication())

    clientHTTP.listen(port)
    workerHTTP.listen(workerPort)

    print >>sys.stderr, "NPSGD server running on port %d" % clientPort
    print >>sys.stderr, "NPSGD worker server running on port %d" % workerPort

    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()
