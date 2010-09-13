#!/usr/bin/python
# make templated docs
# thomasballinger@gmail.com

import os, sys, optparse
import datetime
import calendarhours as hours
import gssltask as task
from pprint import pprint
from jinja2 import Environment, FileSystemLoader
import webbrowser
import tempfile
import datetime

scriptDir = os.path.dirname(os.path.abspath(__file__))
templateDir = scriptDir + '/templates'
env = Environment(loader=FileSystemLoader(templateDir))

def viewTemplated(templateFile, **args):
    if not 'filename' in args:
        (n, fname) = tempfile.mkstemp()
        f = os.fdopen(n, "w")
    else:
        if 'filename' in args and args['filename'] == None:
            (n, fname) = tempfile.mkstemp()
            f = os.fdopen(n, "w")
        else:
            fname = args['filename']
            f = open(fname, "w")
    template = env.get_template(templateFile)
    f.write(template.render(**args))
    f.close()
    webbrowser.open(fname)

def showTasks():
    viewTemplated('showTasks.html', task_list=task.createTasks())

def sortTasksByTime(task_list):
    task_list.sort(key = lambda t: -t.weekHours)
    return task_list

def showWeekly(ds1, ds2, filename=None):
    task_list = task.createTasks()
    totalHours = datetime.timedelta(0)
    for t in task_list:
        t.timeToGo = (t.estimatedtime - t.timespent)
        t.timeTillDue = (t.duedate - datetime.datetime.now())
    for t in task_list:
        t.weekHours = hours.get_week_hours(t.id, ds1, ds2)
        totalHours += t.weekHours
    weekList = [x for x in task_list if x.weekHours > datetime.timedelta(0)]
    assigners = {}
    for t in weekList:
        if not t.assigner in assigners:
            assigners[t.assigner] = t.weekHours
        else:
            assigners[t.assigner] += t.weekHours
    assigners = zip(assigners.keys(), assigners.values())
    assigners.sort(key = lambda t: -t[1])
    viewTemplated('weekHours.html', filename=filename,
            task_list=task_list,
            week_list=weekList,
            assigners=assigners,
            ds1=ds1, ds2=ds2,
            td2h=task.timedeltaToHoursString,
            td2jh=task.timedeltaToJustHoursString,
            td2d=task.timedeltaToDaysString,
            zeroHours = datetime.timedelta(0),
            timesort=sortTasksByTime,
            total_hours=totalHours)

def showTask(taskid):
    tasks = task
    viewTemplated('notImplemented.html', task_list)
    pass

def showInProgress():
    viewTemplated('notImplemented.html', task_list)
    pass

def showProjects():
    task_list = [f for t in self.task_list if not t.iscompleted]
    task_list.sort(key=lambda t: t.assigner)
    for t in task_list:
        t.timeToGoString = hours.timedeltaToHoursString(t.estimatedtime - t.timespent)
        t.timeTillDueString = hours.timedeltaToHoursString(t.duedate - datetime.datetime.now())
    viewTemplated('projects.html', task_list=task_list)
    pass

def showOverdue():
    viewTemplated('notImplemented.html', task_list)
    pass

if __name__ == '__main__':
#    showTasks()
#    SHOWweekly('2010-07-12','2010-07-21')
    showWeekly('2010-07-19','2010-07-26')
