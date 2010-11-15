import os
import sys

class Config(object):
    def __init__(self):
        self.serverAddress    = "127.0.0.1"
        self.serverPort       = 8000
        self.serverWorkerPort = 8001

def readDefaultConfig():
    return readConfig("config.txt")

def readConfig(textFile):
    return Config()
