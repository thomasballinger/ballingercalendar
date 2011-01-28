# task.py by ThomasBallinger@gmail.com

import datetime
import abstracttask
import jutdaapi

class Task(abstracttask.Task): # should inherit from base abstract class, which has all att's common to both implementations
    """Represents a task"""
    def __init__(self):
        """Creates a local new task"""
#        self.id = '' # this is the id used in calendars, etc.
        self._ticket_id = ''# this is an implementation detail of jutda task tracker
#        self.whose = 'no one' # who task is assigned to, in this implementation
#        self.name = 'unnamed' # ticket title, in this implementation
#        self.description = 'no description' # unencoded version, so no <br>'s (but stil <a href>x<a>'s)
                                            # also includes followup data, appended to this in a nice print format
#        self.assigner = 'no one' # capitalized, should be found in every title (like "Multiword Title F/for: Person")
#        self.priority = 9 # number from 0 to 9, but stored as a number from 1 to 5.  Always (n-1)*2 or (n+1)/2
        self.estimatedtime = datetime.timedelta(0,60*60) # not a field stored, so should be deleted
#        self.timespent = datetime.timedelta(0) # not editable permenently, but saves data from hours
#        self.starttime = datetime.datetime.now() # ticket creation time in this implementation 
        self.isappointment = False # always false for these
        self.followups = [] # not likely to be used, since other implementation doesn't have it.

    def __repr__(self):
        """not for general use"""
        return 'jutdatask: '+self.name

    def __cmp__(a,b):
        td = b.duedate - a.duedate
        return td.days * 24*60*60 + td.seconds

    def put(self):
        updateTask(self)

def createTasks():
    """Returns a (full) list of task objects"""
    tickets = jutdaapi.get_tickets() # this works better (still not
                                     # perfect) if list results is
                                     # to 1000 in jutda user settings
    for ticket in tickets:
        task = Task()
        task.
    tasks = []
    return tasks

def updateTask(task):
    """Updates the database task with local information, perhaps creating a new one"""
    # First check to see if task exists
    # If so, check that things have actually changed
    # If so, edit through the api for minor things,
    # otherwise use the detail scrape interface.
    raise NotImplementedError('delete that row, move everything up')

def importanceUrgencyGraph(task_list):
    """Returns a list of [task,[duedate, Importance]] items"""
    firstDueDate = min([x.duedate for x in task_list])
    lastDueDate = max([x.duedate for x in task_list])
    now = min([x.duedate for x in task_list])
    return [[x.name,[x.duedate,x.priority]] for x in task_list]

def deleteTask(task):
    """Deletes the task via the api"""
    raise NotImplementedError('Easy to implement, a bit dangerous though')

def newTask(name, whose=None):
    """Creates a new ticket in the database too"""
    t = Task()
    if whose:
        # finduser api call to see if user exists
        t.whose = whose
    t.name = name
    updateTask(t)
    return t

def displayTask(task):
    raise NotImplementedError('some sort of nice text display')

def updateTimeSpent(task):
    raise NotImplementedError('check google calendar for matching events')

