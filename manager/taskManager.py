from django.core import serializers
from manager.models import *
from manager import views
from .requestHandler import requestHandler as rh
import os
import re
import time
import random
import json
import html

class taskManager:

    def __init__(self):
        pass


    def task_manager(self):
        while True:
            if self.resource_available()
                self.executeNextTask()
            self.checkUpdateTaskStatus()
            sleep(1)


    def resource_available(self):
        #check cpu & ram if they're within limits
        return True


    def executeNextTask(self):
        task = self.getNextTask()
        self.linkInputData(task)
        self.linkStepFiles(task)
        self.completeRawScript(task)
        self.startProcess(task)
        self.updateDbFields(task)


    def checkUpdateTaskStatus(self):
        running, finished, failed = checkRunningScripts()
        self.fixBroken(failed)
        self.makePostRun(finished)


    def getNextTask(self):
        pass

    def linkInputData(self, task):
        pass

    def linkStepFiles(self, task):
        pass

    def completeRawScript(self, task):
        pass

    def startProcess(self, task):
        pass

    def updateDbFields(self, task):
        pass

    def fixBroken(self, failed):
        pass

    def makePostRun(self, finished):
        pass








    #these will be executed just before a task starts:
    #task_folder = views.requestNewFolder(self.username, 'task')
    #new_input_files = self.linkInputFiles(input_files, task_folder)

    #task manager should perform this at the time of execution
    #! a task might be dependent on an uncompleted task
    def linkInputFiles(self, input_files, folder):
        new_input_files = []
        for file in input_files:
            try:
                os.symlink(file, folder+file.split("/")[-1])
                new_input_files.append(folder+file.split("/")[-1])
            except Exception as e:
                print('Error:{} for {}'.format(file, e))
        return new_input_files
