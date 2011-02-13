# task.py by ThomasBallinger@gmail.com

import re
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
import auth
import webbrowser
import abstracttask

(email, password) = auth.get_authentication('gmailaddress', 'gmailpassword')
spreadsheet = 'tasks'
worksheet = 'Sheet1'
googleCalendarZero = datetime.datetime(1899,12,30)

class Task(abstracttask.Task):
    def __init__(self):
        abstracttask.Task.__init__(self)
        self.duedate = datetime.datetime.now()
        self.estimatedtime = datetime.timedelta(0,60*60)
        self.waitids = []
        self.isappointment = False
        self.row = None

    def __repr__(self):
        return 'gssltask: '+self.name+' '+str(self.duedate)

    def __cmp__(a,b):
        td = b.duedate - a.duedate
        return td.days * 24*60*60 + td.seconds

    def put(self):
        updateTask(self)
    def getPropDict(self):
        propDict = {
            'id' : self.id ,
            'whose' : self.whose ,
            'name' : self.name ,
            'description' : self.description ,
            'assigner' : self.assigner ,
        }
        propDict['priority'] =  str(self.priority)
        propDict['waitids'] = ' '.join(self.waitids)
        propDict['duedate'] = str(datetimeToGoogleNum(self.duedate))
        propDict['estimatedtime'] = str(timedeltaToGoogleNum(self.estimatedtime))
        propDict['timespent'] = str(timedeltaToGoogleNum(self.timespent))
        propDict['starttime'] = str(datetimeToGoogleNum(self.starttime))
        if self.isappointment:
            propDict['isappointment'] = 'TRUE'
        else:
            propDict['isappointment'] = 'FALSE'
        if self.iscompleted:
            propDict['iscompleted'] = 'TRUE'
        else:
            propDict['iscompleted'] = 'FALSE'
        return propDict

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

def getClient():
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.source = 'Task Google Spreadsheet Storage'
    try:
        gd_client.ProgrammaticLogin()
    except gdata.service.CaptchaRequired:
        print gdata.service.CaptchaRequired, 'exception raised'
        captcha_token = gd_client._GetCaptchaToken()
        url = gd_client._GetCaptchaURL()
        print "Please go to this URL:"
        print "  " + url
        webbrowser.open(url)
        captcha_response = raw_input("Type the captcha image here: ")
        gd_client.ProgrammaticLogin(captcha_token, captcha_response)
        print "Done!"
    return gd_client

def createTasks():
    """Returns a list of task objects"""
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
        task.timespent = googleNumToTimedelta(float(entry.cell.numericValue))
    elif prop in ['starttime', 'start time', 'Starttime', 'Start Time']:
        task.starttime = googleNumToDatetime(float(entry.cell.numericValue))
    elif prop in ['waitids', 'wait ids', 'Wait IDs', 'Waitids']:
        task.waitids = entry.cell.inputValue.split()
    elif prop in ['appointment', 'isappointment', 'is appointment', 'Is Appointment']:
        if entry.cell.inputValue in ['TRUE']:
            task.isappointment = True
        elif entry.cell.inputValue in ['FALSE']:
            task.isappointment = False
    elif prop in ['complete', 'isComplete', 'iscomplete', 'is complete','iscompleted','isCompleted','is completed']:
        if entry.cell.inputValue in ['TRUE']:
            task.iscompleted = True
        elif entry.cell.inputValue in ['FALSE']:
            task.iscompleted = False
    else:
        print 'unknown property',entry.cell.inputValue,'in column',prop

def updateTask(task):
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.source = 'Task Google Spreadsheet Storage'
    gd_client.ProgrammaticLogin()
    (spreadsheetID, worksheetID) = getTasksIDs(gd_client)
    q = gdata.spreadsheet.service.ListQuery()
    if task.id:
        q.sq = 'id='+task.id
        feed = gd_client.GetListFeed(spreadsheetID, worksheetID, query=q)
    if task.id and feed:
        rowFeed = feed.entry[0]
        entry = gd_client.UpdateRow(rowFeed, task.getPropDict())
        if not isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
            raise Error('Edit appears to have failed')
    else:
        # creating new task
        if task.id:
            pass # we don't need to find a new id
        else:
            q2 = gdata.spreadsheet.service.ListQuery()
            q2.orderby='column:id'
            q2.reverse = 'true'
            idfeed = gd_client.GetListFeed(spreadsheetID, worksheetID, query=q2)
            if idfeed:
                match = re.search(r'id: ([^,]+)',idfeed.entry[0].content.text)
                task.id = str(int(match.group(1)) + 1)
            else:
                print 'no ids found'
                task.id = '1'
        entry = gd_client.InsertRow(task.getPropDict(), spreadsheetID, worksheetID)
        if not isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
            raise Error('Insert row appears to have failed')

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

def getTheStack(task_list):
    stack = [x for x in task_list if not x.iscompleted]
    stack.sort()
    return task_list

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

def timedeltaToDaysString(td):
    if abs(td) < datetime.timedelta(1):
        output = str(abs(td).seconds / 3600)+':'+('00'+str(abs(td).seconds / 60))[-2:]
    else:
        output = str(abs(td).days)+' days'
#        output = str(abs(td).days)+' days, '+('00'+str(abs(td).seconds / 3600))[-2:]+':'+('00'+str(abs(td).seconds / 60))[-2:]
    if td < datetime.timedelta(0):
        # overdue timedelta
        return 'overdue by '+output
    else:
        return output

def timedeltaToHoursString(td):
    s = td.seconds +  24 * 60 * 60 * td.days
    h = s / 60 / 60
    m = int(s / 60 % 60)
    return str(h)+':'+('00'+str(m))[-2:]

def timedeltaToJustHoursString(dt):
    s = dt.days * 24 * 3600 + dt.seconds
    h = float(s) / 3600
    return '%.1f' % h + ' hours'

if __name__ == '__main__':
#    newTask('asdf asdfas dadsfati ng')
#    task_list = createTasks()
#    import pprint
#    pprint.pprint(task_list)
#    for task in task_list:
#        task.put()    
    from pprint import pprint
    pprint(createTasks())
