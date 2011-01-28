# abstracttask.py by ThomasBallinger@gmail.com

import datetime

class Task(object):
    """Represents a task, with task associated logic"""
    def __init__(self):
        """Creates a local new task"""
        self.id = '' # this is the id used in calendars, not for any task implementation
        self.whose = 'no one'
        self.name = 'unnamed'
        self.description = 'no description'
        self.assigner = 'no one'
        self.priority = 9 # number from 0 to 9, but stored as a number from 1 to 5.  Always (n-1)*2 or (n+1)/2
        self.timespent = datetime.timedelta(0) # populated by an hours implementation, not by the task imp.
        self.starttime = datetime.datetime.now() # reasonable value, but overwriting this
                                                 # with a time from a database is better
        self.iscompleted = False # directly maps to status, but marking as complete requires a message

    def __repr__(self):
        """not for general use"""
        return 'abstract task: '+self.name

    def __cmp__(a,b):
        return b.priority - a.priority

    def put(self):
        """Somehow stores the task"""
        raise NotImplemented("Backend dependent")

def displayTask(task):
    raise NotImplementedError('some sort of nice text display')
