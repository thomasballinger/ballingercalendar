# task.py by ThomasBallinger@gmail.com

import os
import datetime
try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import string
import time
import auth

(email, password) = auth.getAuthentication()
spreadsheet = 'tasks'
worksheet = 'Sheet1'
googleCalendarZero = datetime.datetime(1900,12,30)
idstringfront = '%$&task&$%-%$#'
idstringback  = '#$%'

def getClient():
    cal_client = gdata.calendar.service.CalendarService()
    cal_client.email = email
    cal_client.password = password
    cal_client.source = 'name of app?'
    cal_client.ProgrammaticLogin()
    return cal_client

def getWorkHours(startdate, enddate):
    raise NotImplementedError('Will return the when on the planned work calendar has events')

def getUnscheduledWorkHours(startdate, enddate):
    raise NotImplementedError('work hours minus scheduled appointments')

def getHoursWorked(taskid):
    '''Returns just a timedelta object representing time spend on task'''
    idstring = idstringfront + taskid + idstringback
    cal_client = getClient()
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', idstring)
    feed = cal_client.CalendarQuery(query)
    hours = datetime.timedelta(0)
    for i, event in zip(range(len(feed.entry)), feed.entry):
        for when in event.when:
            start = googleCalTimeToDatetime(when.start_time)
            end =  googleCalTimeToDatetime(when.end_time)
            td = end - start
            hours += td
    return hours

def googleCalTimeToDatetime(gcaltime):
    (date, time) = gcaltime.split('T')
    (time,timezone) = time.split('-')
    (year, month, day) = date.split('-')
    (hours, minutes, seconds) = time.split(':')
    (seconds, milliseconds) = seconds.split('.')
    return datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes), int(seconds))

def clockTime(taskid, title=None, description='', startDatetime=None, endDatetime=None):
    if title is None:
        title = 'hours clocked'
    cal_client = getClient()
    content = description + '/n' + idstringfront + taskid + idstringback
    event = gdata.calendar.CalendarEventEntry()
    event.title = atom.Title(text=title)
    event.content = atom.Content(text=content)

    if startDatetime is None:
        # Use current time for the end_time and have the event last 1 hour
        start_time = time.strftime('%Y-%m-%dT%H:00:00.000Z', time.gmtime(time.time() - 3600))
        end_time = time.strftime('%Y-%m-%dT%H:00:00.000Z', time.gmtime(time.time()))
    elif endDatetime is None:
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime((startDatetime + datetime.timedelta(0,3600)).timetuple()))
    else:
        start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(startDatetime.timetuple()))
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(endDatetime.timetuple()))
    event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))
    new_event = cal_client.InsertEvent(event, '/calendar/feeds/default/private/full')
    #print 'New single event inserted: %s' % (new_event.id.text,)
    #print '\tEvent edit URL: %s' % (new_event.GetEditLink().href,)
    #print '\tEvent HTML URL: %s' % (new_event.GetHtmlLink().href,)
    return new_event

if __name__ == '__main__':
    print(getHoursWorked('4'))
    clockTime('4',title='Working on that thing')
    print(getHoursWorked('4'))
