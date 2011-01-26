# task.py by ThomasBallinger@gmail.com

import datetime
import auth

USER = 'tomb'
SERVER = 'http://pnl-t75-1.bwh.harvard.edu:9000'

def getPassword():
    user, password = auth.get_authentication()
    return password

class Task:
    """Represents a task"""
    def __init__(self):
        """Creates a local new task"""
        self.id = ''
        self.whose = 'no one'
        self.name = 'unnamed'
        self.description = 'no description'
        self.duedate = datetime.datetime.now()
        self.assigner = 'no one'
        self.priority = 9
        self.estimatedtime = datetime.timedelta(0,60*60)
        self.timespent = datetime.timedelta(0)
        self.starttime = datetime.datetime.now()
        self.waitids = []
        self.isappointment = False
        self.iscompleted = False
        self.row = None

    def __repr__(self):
        return 'task: '+self.name

    def __cmp__(a,b):
        td = b.duedate - a.duedate
        return td.days * 24*60*60 + td.seconds

    def put(self):
        updateTask(self)

def createTasks():
    '''Returns a (full) list of task objects'''
    gd_client = getClient()
    (spreadsheetID, worksheetID) = getTasksIDs(gd_client)
    cellsFeed = gd_client.GetCellsFeed(spreadsheetID, worksheetID)
    if not isinstance(cellsFeed, gdata.spreadsheet.SpreadsheetsCellsFeed):
        return False
    tasks = []
    colDict = {}
    task = None
    oldrow = '0'
    for i, entry in enumerate(cellsFeed.entry):
        if entry.cell.row == '1':
            # set up params for reading
            colDict[entry.cell.col] = entry.content.text
        elif entry.cell.row != oldrow:
            task = Task()
            tasks.append(task)
            addPropToTask(task, entry, colDict)
            oldrow = entry.cell.row
        else:
            addPropToTask(task, entry, colDict)
    return tasks

def updateTask(task):
    """Updates the database task with local information"""
    raise NotImplementedError('delete that row, move everything up')

def importanceUrgencyGraph(task_list):
    """Returns a list of [task,[duedate, Importance]] items"""
    firstDueDate = min([x.duedate for x in task_list])
    lastDueDate = max([x.duedate for x in task_list])
    now = min([x.duedate for x in task_list])
    return [[x.name,[x.duedate,x.priority]] for x in task_list]

def deleteTask(task):
    raise NotImplementedError('delete that row, move everything up')

def newTask(name):
    t = Task()
    t.name = name
    t.id = ''
    updateTask(t)
    return t

def displayTask(task):
    raise NotImplementedError('some sort of nice text display')

def updateTimeSpent(task):
    raise NotImplementedError('check google calendar for matching events')

