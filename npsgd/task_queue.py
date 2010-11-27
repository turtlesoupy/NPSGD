import os
import sys
import logging

class TaskQueueException(RuntimeError): pass

class TaskQueue(object):
    def __init__(self):
        self.requests        = []
        self.processingTasks = []

    def putTask(self, request):
        self.requests.append(request)
        logging.info("Added task to model queue as number %d", len(self.requests))

    def putProcessingTask(self, task):
        self.processingTasks.append(task)

    def pullNextTask(self):
        return self.requests.pop(0)

    def pullProcessingTaskById(self, taskId):
        possibleTasks = [e for e in self.processingTasks if e.taskId == taskId]
        self.processingTasks = [e for e in self.processingTasks if e.taskId != taskId]

        return possibleTasks[0]



    def isEmpty(self):
        return len(self.requests) == 0
