# hours.py by ThomasBallinger@gmail.com

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

from pprint import pprint

(email, password) = auth.getAuthentication()
googleCalendarZero = datetime.datetime(1900,12,30)
idstringfront = 'qyvztaskqyvz qyvz'
idstringback  = 'qyvz'

def getClient():
    # Add a way to get a web-type client
    cal_client = gdata.calendar.service.CalendarService()
    cal_client.email = email
    cal_client.password = password
    cal_client.source = 'name of app?'
    cal_client.ProgrammaticLogin()
    return cal_client

def getWorkHours(startdate, enddate):
    """Returns a list of (datetime.datetime, datetime.timedelta) pairs describing future work plans"""
    cal_client = getClient()
    query = gdata.calendar.service.CalendarEventQuery('work-schedule', 'private', 'full')
    #raise NotImplementedError('Will return the when on the planned work calendar has events')

def getUnscheduledWorkHours(startdate, enddate):
    raise NotImplementedError('work hours minus scheduled appointments')

def getHoursWorked(taskidList):
    if type(taskidList) != type([]):
        return getHoursWorkedSingle
    raise Exception("This doesn't actually make that much sense; the feed has some max length")

def getHoursWorkedSingle(taskid):
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

def testSearch(text):
    cal_client = getClient()
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', text)
    feed = cal_client.CalendarQuery(query)
    for event in feed.entry:
        print event.title.text

def getWeekHours(taskidList, ds1=None, ds2=None):
    if type(taskidList) != type([]):
        return getWeekHoursSingle(taskidList, ds1, ds2)
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    if not ds1:
        raise Exception('not implemented yet')
    idstrings = [idstringfront + id + idstringback for id in taskidList]
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', idstringfront)
    query.start_min = ds1
    query.start_max = ds2
    feed = cal_client.CalendarQuery(query)
    raise Exception("Check how max results works before using this")

def getWeekHoursSingle(taskid, ds1=None, ds2=None):
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    if not ds1:
        raise Exception('not implemented yet')
    idstring = idstringfront + taskid + idstringback
    cal_client = getClient()
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', idstring)
    query.start_min = ds1
    query.start_max = ds2
    feed = cal_client.CalendarQuery(query)

    hours = datetime.timedelta(0)
    for i, event in zip(range(len(feed.entry)), feed.entry):
        for when in event.when:
            start = googleCalTimeToDatetime(when.start_time)
            end =  googleCalTimeToDatetime(when.end_time)
            td = end - start
            hours += td
            print event.title.text,start,end
    return hours
    
def googleCalTimeToDatetime(gcaltime):
    try:
        (date, time) = gcaltime.split('T')
    except:
        (year, month, day) = gcaltime.split('-')
        return datetime.datetime(int(year), int(month), int(day))
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

def updateEvent(service, event, newDescription):
    oldDescription = event.content.text
    event.content.text = newDescription

if __name__ == '__main__':
#    from pprint import pprint
#    start = datetime.datetime.now()
#    end = start + datetime.timedelta(10)
#    pprint(getWorkHours(start, end))
#    print getWeekHours('10','2010-07-05', '2010-07-24')

    testSearch('qyvz'+'10'+'qyvz')





#     #code for changing the idstrings we use to identify tasks 
#
#    cal_client = getClient()
#    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', idstringfront)
#    query.max_results = 1000
#    feed = cal_client.CalendarQuery(query)
#
#    for event in feed.entry:
#        print event.title.text
#        oldDescription = event.content.text
#        newDescription = oldDescription.replace(idstringfront,'\nqyvztaskqyvz qyvz').replace(idstringback,'qyvz')
#        event.content.text = newDescription
#        result = cal_client.UpdateEvent(event.GetEditLink().href, event)
#        #raw_input('Did it work?')


