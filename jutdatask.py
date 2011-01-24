# task.py by ThomasBallinger@gmail.com

import datetime
import urllib
import auth

USER = 'tomb'

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

def getPassword():
    user, password = auth.get_authentication()
    return password

def getUserID(user):
    """Returns an a string id that is the user's Task Tracker ID"""
    query = user
    data = urllib.urlencode({"username" : query, "user" : USER, "password" : getPassword()})
    f = urllib.urlopen("http://pnl-t75-1.bwh.harvard.edu:9000/api/find_user/", data)
    s = f.read()
    f.close()
    return s

def create_ticket(queue, title, submitter_email=None, assigned_to=None, priority=None):
    """Creates a new Task Tracker Ticket"""
    datadict = {"username" : query, "user" : USER, "password" : getPassword()}
    if submitter_email:
        datadict["submitter_email"] = submitter_email
    if assigned_to:
        try:
            trash = int(assigned_to)
            datadict["assigned_to"] = assigned_to
        except ValueError:
            datadict["assigned_to"] = getUserId(assigned_to)
    if priority:
        datadict["priority"] = priority
    data = urllib.urlencode()
    f = urllib.urlopen("http://pnl-t75-1.bwh.harvard.edu:9000/api/find_user/", data)
    s = f.read()
    f.close()
    return s

def delete_ticket(ticket, confirm):
    """Entirely deletes the ticket"""
    raise NotImplemented("This could be dangerous (but wrong permissions anyway)")

def hold_ticket(ticket):
    """Places a ticket on hold, preventing it from being escalated"""
    raise NotImplemented("I don't think we use this functionality")

def unhold_ticket(ticket):
    """Removes a ticket from hold"""
    raise NotImplemented("I don't think we use this functionality")

def getUserID(user):
    """Returns an a string id that is the user's Task Tracker ID"""
    query = user
    data = urllib.urlencode({"username" : query, "user" : USER, "password" : getPassword()})
    f = urllib.urlopen("http://pnl-t75-1.bwh.harvard.edu:9000/api/find_user/", data)
    s = f.read()
    f.close()
    return s

def add_followup(ticket, message, public=None):
    """Returns an a string id that is the user's Task Tracker ID"""
    query = user
    datadict = {"username" : query, "user" : USER, "password" : getPassword()}
    if submitter_email:
        datadict["submitter_email"] = submitter_email
    data = urllib.urlencode(datadict)
    f = urllib.urlopen("http://pnl-t75-1.bwh.harvard.edu:9000/api/find_user/", data)
    s = f.read()
    f.close()
    return s


if __name__ == '__main__':
    #newTask('asdf asdfas dadsfati ng')
    #task_list = createTasks()
    #import pprint
    #pprint.pprint(task_list)
    #for task in task_list:
    #    task.put()
    #from pprint import pprint
    #pprint(createTasks())

    # Search the Vaults of Parnassus for "XMLForms".
    # First, encode the data.
    #import pudb; pudb.set_trace()
    print getUserID('tomb')

