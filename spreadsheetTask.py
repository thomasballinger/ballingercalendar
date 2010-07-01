# task.py by ThomasBallinger@gmail.com

import os
import datetime
try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import gdata.spreadsheet.service
import gdata.service
import atom.service
import gdata.spreadsheet
import atom
import getopt
import sys
import string

email = 'thomasballinger'
password = 'tegdirbevoli'
spreadsheet = 'tasks'
worksheet = 'Sheet1'
googleCalendarZero = datetime.datetime(1900,12,30)

class Task:
    def __init__(self):
        self.id = 0 
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
        self.isAppointment = False
        self.isCompleted = False
        self.row = None

    def put(self):
        updateTask(self)
    
    def __repr__(self):
        return 'task: '+self.name+' '+str(self.duedate)

def datetimeToGoogleNum(dt):
    #print dt,'of type',type(dt),'is the input to datetimeToGoogle'
    td = (dt - googleCalendarZero) 
    #print 'producing',td,'which is in seconds from', googleCalendarZero 
    gdays = td.days + float(td.seconds) / (24 * 60 * 60)
    return gdays

def googleNumToDatetime(gdays):
    dt = datetime.timedelta(gdays) + googleCalendarZero
    return dt

def googleNumToTimedelta(gdays):
    td = datetime.timedelta(gdays)
    return td

def timedeltaToGoogleNum(td):
    gdays = td.days + float(td.seconds) / 60 / 60 / 24 + float(td.microseconds) / 1000000 / 60 / 60 / 24
    return gdays

def createTasks():
    '''Returns a list of task objects'''
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.source = 'Task Google Spreadsheet Storage'
    gd_client.ProgrammaticLogin()
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

def addPropToTask(task, entry, colDict):
    prop = colDict[entry.cell.col]
    task.row = entry.cell.row
    if prop in ['id', 'ID', 'Id']:
        task.id = entry.cell.inputValue
    elif prop in ['whose', 'Whose', 'person']:
        task.whose = entry.cell.inputValue
    elif prop in ['name', 'Name', 'title', 'Title']:
        task.name = entry.cell.inputValue
    elif prop in ['desc', 'description', 'Description', 'Desc']:
        task.description = entry.cell.inputValue
    elif prop in ['duedate','due date', 'Duedate', 'dueDate']:
        task.duedate = googleNumToDatetime(float(entry.cell.numericValue))
    elif prop in ['assigner', 'Assigner', 'Assigned By', 'assigned by']:
        task.assigner = entry.cell.inputValue
    elif prop in ['priority', 'Priority', 'Importance', 'importance']:
        task.priority = int(float(entry.cell.numericValue))
    elif prop in ['estimatedtime', 'estimated time', 'Estimated Time', 'Estimatedtime']:
        task.estimatedtime = googleNumToTimedelta(float(entry.cell.numericValue)) 
    elif prop in ['timespent', 'time spent', 'Timespent', 'Time Spent']:
        task.timespent = googleNumToTimedelta(int(float(entry.cell.numericValue)))
    elif prop in ['starttime', 'start time', 'Starttime', 'Start Time']:
        task.starttime = googleNumToDatetime(int(float(entry.cell.numericValue)))
    elif prop in ['waitids', 'wait ids', 'Wait IDs', 'Waitids']:
        task.waitids = entry.cell.inputValue.split()
    elif prop in ['appointment', 'isappointment', 'is appointment', 'Is Appointment']:
        if entry.cell.inputValue in ['TRUE']:
            task.isAppointment = True
        elif entry.cell.inputValue in ['FALSE']:
            task.isAppointment = False
    elif prop in ['complete', 'isComplete', 'iscomplete', 'is complete','iscompleted','isCompleted','is completed']:
        if entry.cell.inputValue in ['TRUE']:
            task.isCompleted = True
        elif entry.cell.inputValue in ['FALSE']:
            task.isCompleted = False
    else:
        print 'unknown property',entry.cell.inputValue,'in column',prop

def updateTask(task):
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.source = 'Task Google Spreadsheet Storage'
    gd_client.ProgrammaticLogin()
    (spreadsheetID, worksheetID) = getTasksIDs(gd_client)

    cellsFeed = gd_client.GetCellsFeed(spreadsheetID, worksheetID)
    propDict = {}
    for i, entry in enumerate(cellsFeed.entry):
        if entry.cell.row == '1':
            # set up params for reading
            propDict[entry.content.text] = entry.cell.col
        else:
            break

    if not task.row:
        raise NotImplementedError('Need to check to find first unused spot in spreadsheet')

    for col, prop in zip(propDict.values(), propDict.keys()):
        if prop in ['id', 'ID', 'Id']:
            value = task.id
        elif prop in ['whose', 'Whose', 'person']:
            value = task.whose
        elif prop in ['name', 'Name', 'title', 'Title']:
            value = task.name
        elif prop in ['desc', 'description', 'Description', 'Desc']:
            value = task.description
        elif prop in ['duedate','due date', 'Duedate', 'dueDate']:
            value = str(datetimeToGoogleNum(task.duedate))
        elif prop in ['assigner', 'Assigner', 'Assigned By', 'assigned by']:
            value = task.assigner
        elif prop in ['priority', 'Priority', 'Importance', 'importance']:
            value = str(task.priority)
        elif prop in ['estimatedtime', 'estimated time', 'Estimated Time', 'Estimatedtime']:
            value = str(timedeltaToGoogleNum(task.estimatedtime))
        elif prop in ['timespent', 'time spent', 'Timespent', 'Time Spent']:
            value = str(timedeltaToGoogleNum(task.timespent))
        elif prop in ['starttime', 'start time', 'Starttime', 'Start Time']:
            value = str(datetimeToGoogleNum(task.starttime))
        elif prop in ['waitids', 'wait ids', 'Wait IDs', 'Waitids']:
            value = ' '.join(task.waitids)
        elif prop in ['appointment', 'isappointment', 'is appointment', 'Is Appointment']:
            if task.isAppointment:
                value = 'TRUE'
            else:
                value = 'FALSE'
        elif prop in ['complete', 'isComplete', 'iscomplete', 'is complete','iscompleted','isCompleted','is completed']:
            if task.isCompleted:
                value = 'TRUE'
            else:
                value = 'FALSE'
        else:
            print 'unknown property',prop,'in column',col
        print 'now updating task',task.id,prop,'with value',value 
        entry = gd_client.UpdateCell(row=task.row, col=col, inputValue=value, key=spreadsheetID, wksht_id=worksheetID)

def getTasksIDs(gd_client):
    index = None
    feed = gd_client.GetSpreadsheetsFeed()
    for i, entry in enumerate(feed.entry):
        if entry.title.text == spreadsheet:
            index = i
            id_parts = feed.entry[i].id.text.split('/')
            spreadsheetID = id_parts[-1]
            break
    if index == None:
        print 'spreadsheet not found'
        return False
    
    index = None
    feed = gd_client.GetWorksheetsFeed(spreadsheetID)
    for i, entry in enumerate(feed.entry):
        if entry.title.text == worksheet:
            index = i
            id_parts = feed.entry[i].id.text.split('/')
            worksheetID = id_parts[-1]
            break
    if index == None:
        print 'worksheet not found'
        return False

    return (spreadsheetID, worksheetID)

def printFeed(feed):
    for i, entry in enumerate(feed.entry):
        if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
            print '%s %s\n' % (entry.title.text, entry.content.text)
        elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
            print '%s %s %s' % (i, entry.title.text, entry.content.text)
            # Print this row's value for each column (the custom dictionary is
            # built using the gsx: elements in the entry.)
            print 'Contents:'
            for key in entry.custom:  
                print '  %s: %s' % (key, entry.custom[key].text) 
            print '\n',
        else:
            print '%s %s\n' % (i, entry.title.text)

def getTheStack(taskList):
    stack = [x for x in taskList if not x.isCompleted]
    stack.sort()
    return taskList

def importanceUrgencyGraph(taskList):
    """Returns a list of [task,[duedate, Importance]] items"""
    firstDueDate = min([x.duedate for x in taskList])
    lastDueDate = max([x.duedate for x in taskList])
    now = min([x.duedate for x in taskList])
    return [[x.name,[x.duedate,x.priority]] for x in taskList]

def deleteTask(task):
    raise NotImplementedError('delete that row, move everything up')

def newTask(name):
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.source = 'Task Google Spreadsheet Storage'
    gd_client.ProgrammaticLogin()
    (spreadsheetID, worksheetID) = getTasksIDs(gd_client)

    cellsFeed = gd_client.GetCellsFeed(spreadsheetID, worksheetID)
    maxRow = '1'
    maxid = '0'
    idRow = '0'
    for i, entry in enumerate(cellsFeed.entry):
        if entry.cell.row == 1:
            if entry.cell.inputValue in ['id', 'ID', 'Id']:
                idRow = entry.cell.col
        else:
            if int(entry.cell.row) > int(maxRow):
                maxRow = entry.cell.row
            if entry.cell.col == idRow:
                if int(entry.cell.inputValue) > int(maxid):
                    maxid = entry.cell.inputValue
    row = str(int(maxRow) + 1)
    id = str(int(maxid) + 1)
    task = Task()
    task.name = name
    task.id = id
    task.row = row
    task.put()

def displayTask(task):
    raise NotImplementedError('some sort of nice text display')

def updateTimeSpent(task):
    raise NotImplementedError('check google calendar for matching events')

if __name__ == '__main__':
    newTask('asdfdoSoafdmetsdafhingINteresting')
    taskList = createTasks()
    import pprint
    pprint.pprint(taskList)
#    for task in taskList:
#        task.put()
        
