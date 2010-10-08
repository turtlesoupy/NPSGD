import os
import sys

class NPSGDConfig(object):
    def __init__(self):
        self.serverAddress = "127.0.0.1"
        self.serverPort    = 8000

def readDefaultConfig():
    return readConfig("config.txt")

def readConfig(textFile):
    return NPSGDConfig()
