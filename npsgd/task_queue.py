import os
import sys
import time
import logging
import threading

class TaskQueueException(RuntimeError): pass

class TaskQueue(object):
    def __init__(self):
        self.requests        = []
        self.processingTasks = []
        self.lock = threading.RLock()

    def putTask(self, request):
        with self.lock:
            self.requests.append(request)

        logging.info("Added task to model queue as number %d", len(self.requests))


    def putProcessingTask(self, task):
        now = time.time()
        with self.lock:
            self.processingTasks.append((task, now))

    def pullNextTask(self):
        with self.lock:
            return self.requests.pop(0)

    def touchProcessingTaskById(self, taskId):
        now = time.time()
        with self.lock:
            for i, (task, taskTime) in enumerate(self.processingTasks):
                if task.taskId == taskId:
                    self.processingTasks[i] = (task, now)
                    break
            else:
                raise TaskQueueException("Invalid id '%s'" % taskId)

    def hasProcessingTaskById(self, taskId):
        with self.lock:
            return any(e.taskId == taskId for (e,t) in self.processingTasks)

    def pullProcessingTasksOlderThan(self, oldTime):
        with self.lock:
            expireTasks = [e for (e,t) in self.processingTasks if t <= oldTime]
            self.processingTasks = [(e,t) for (e,t) in self.processingTasks if t > oldTime]

            return expireTasks

    def pullProcessingTaskById(self, taskId):
        with self.lock:
            possibleTasks = [e for (e,t) in self.processingTasks if e.taskId == taskId]
            self.processingTasks = [(e,t) for (e,t) in self.processingTasks if e.taskId != taskId]

            if len(possibleTasks) == 0:
                raise TaskQueueException("Invalid id '%s'" % taskId)

            return possibleTasks[0]

    def isEmpty(self):
        with self.lock:
            return len(self.requests) == 0
