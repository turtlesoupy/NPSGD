import tornado.httpserver
import tornado.ioloop
import tornado.web
import sys
import os


class ClientRequest(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class WorkerInfo(tornado.web.RequestHandler):
    def get(self):
        self.write("{}")

class WorkerTaskRequest(tornado.web.RequestHandler):
    def get(self):
        pass


clientApplication = tornado.web.Application([
    (r"/", ClientRequest)
])

workerApplication = tornado.web.Application([
    (r"/info", WorkerInfo)
])


clientPort = 8000
workerPort = 8001

def main():
    port = 8000
    clientHTTP = tornado.httpserver.HTTPServer(clientApplication)
    workerHTTP = tornado.httpserver.HTTPServer(workerApplication)

    clientHTTP.listen(port)
    workerHTTP.listen(workerPort)

    print >>sys.stderr, "NPSGD server running on port %d" % clientPort
    print >>sys.stderr, "NPSGD worker server running on port %d" % workerPort

    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()
