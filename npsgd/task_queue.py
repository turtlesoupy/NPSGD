"""Module containing a 'task queue' for the queue daemon."""
import os
import sys
import time
import logging
import threading

class TaskQueueException(RuntimeError): pass

class TaskQueue(object):
    """Main queue object (thread safe).

    Contains two internal queues: one for actually holding requests, and one
    for holding the tasks that are currently being processed. This way, if 
    a task fails to process we can cycle it back into the requests queue a 
    few times to see if the error was transient.
    """
    def __init__(self):
        self.requests        = []
        self.processingTasks = []
        self.lock = threading.RLock()

    def allRequests(self):
        """Returns all requests in processing or requests queue.
        
        This is really only useful for serializing the queue to disk."""
        with self.lock:
            return self.requests + self.processingTasks


    def putTask(self, request):
        """Puts a model into the queue for worker processing."""
        with self.lock:
            self.requests.append(request)

        logging.info("Added task to model queue as number %d", len(self.requests))


    def putProcessingTask(self, task):
        """Puts a model into the queue for worker processing."""
        now = time.time()
        with self.lock:
            self.processingTasks.append((task, now))

    def pullNextTask(self):
        """Pulls a model from the worker queue."""
        with self.lock:
            return self.requests.pop(0)

    def touchProcessingTaskById(self, taskId):
        """Update timestamp on a task that is currently processing."""

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
        """Pulls tasks out of the processing queue that are stale."""

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
