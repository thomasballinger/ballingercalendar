# hours.py by ThomasBallinger@gmail.com
"""This module contains methods for dealing with hours worked on tasks,
implemented via the user's main Google calendar."""
import re
import datetime
import time

try:      # this is so different versions of python can run this
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom

import auth

(EMAIL, PASSWORD) = auth.get_authentication()
ID_STRING_TASK  = 'qyvztaskqyvz'
ID_STRING_FRONT = 'qyvz'
ID_STRING_BACK  = 'qyvz'

def get_client():
    """Returns a local authenticated client for gdata stuff"""
    # Add a way to get a web-type client
    cal_client = gdata.calendar.service.CalendarService()
    cal_client.email = EMAIL
    cal_client.password = PASSWORD
    cal_client.source = 'ballingercalendar local app'
    cal_client.ProgrammaticLogin()
    return cal_client

#def get_work_hours(startdate, enddate):
#    """Returns a list of (datetime.datetime, datetime.timedelta)
#    pairs describing future work plans"""
#    cal_client = get_client()
#    query = gdata.calendar.service.CalendarEventQuery(
#        'work-schedule', 'private', 'full')
#    raise NotImplementedError('nothing with work hours really works yet')

#def get_unscheduled_work_hours(startdate, enddate):
#    """Returns a list of (datetime.datetime, datetime.timedelta)
#    pairs describing future free work hours"""
#    raise NotImplementedError('work hours minus scheduled appointments')

def get_hours_worked(task_id_list):
    """Returns timedelta object for time spend on task"""
    if type(task_id_list) != type([]):
        return get_hours_worked_single(task_id_list)

def get_hours_worked_single(task_id):
    '''Returns just a timedelta object representing time spend on task'''
    idstring = ID_STRING_TASK + ' ' + ID_STRING_FRONT + task_id + ID_STRING_BACK
    cal_client = get_client()
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', idstring)
    feed = cal_client.CalendarQuery(query)
    hours = datetime.timedelta(0)
    for event in feed.entry:
        for when in event.when:
            start = google_cal_time_to_datetime(when.start_time)
            end =  google_cal_time_to_datetime(when.end_time)
            delta = end - start
            hours += delta
    return hours

def test_search(text):
    """Searches for text in all events in calendar"""
    cal_client = get_client()
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', text)
    feed = cal_client.CalendarQuery(query)
    for event in feed.entry:
        print event.title.text

def get_week_hours(task_id_list=[], ds1=None, ds2=None):
    """Returns the number of hours spend in a time period working on tasks"""
    if type(task_id_list) != type([]):
        return get_week_hours_single(task_id_list, ds1, ds2)
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    if not ds1:
        raise Exception('not implemented yet')
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', ID_STRING_TASK)
    query.start_min = ds1
    query.start_max = ds2
    query.max_results = 1000
    cal_client = get_client()
    feed = cal_client.CalendarQuery(query)
    result_dict = {}
    for event in feed.entry:
        task_id = re.search(
            ID_STRING_TASK+' '+ID_STRING_FRONT+'(.*)'+ID_STRING_BACK,
            event.content.text).group(1)
        hours = datetime.timedelta(0)
        for when in event.when:
            start = google_cal_time_to_datetime(when.start_time)
            end =  google_cal_time_to_datetime(when.end_time)
            delta = end - start
            hours += delta
        if task_id in result_dict:
            result_dict[task_id] += hours
        else:
            result_dict[task_id] = hours
    return result_dict

def get_week_hours_single(task_id, ds1=None, ds2=None):
    """Returns the number of hours worked in a time period on a task"""
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    if not ds1:
        raise Exception('not implemented yet')
    idstring = ID_STRING_TASK + ' ' + ID_STRING_FRONT + task_id + ID_STRING_BACK
    cal_client = get_client()
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', idstring)
    query.start_min = ds1
    query.start_max = ds2
    feed = cal_client.CalendarQuery(query)

    hours = datetime.timedelta(0)
    for event in feed.entry:
        for when in event.when:
            start = google_cal_time_to_datetime(when.start_time)
            end =  google_cal_time_to_datetime(when.end_time)
            td = end - start
            hours += td
            print event.title.text, start, end
    return hours
    
def google_cal_time_to_datetime(gcaltime):
    """Returns a python datetime object from a google calendar time"""
    try:
        (gcal_date, gcal_time) = gcaltime.split('T')
    except ValueError:
        (year, month, day) = gcaltime.split('-')
        return datetime.datetime(int(year), int(month), int(day))
    (gcal_time, timezone) = gcal_time.split('-')
    (year, month, day) = gcal_date.split('-')
    (hours, minutes, seconds) = gcal_time.split(':')
    (seconds, milliseconds) = seconds.split('.')
    return datetime.datetime(
        int(year), int(month), int(day), int(hours),
        int(minutes), int(seconds))

def clock_time(task_id, title=None, description='',
         start_datetime=None, end_datetime=None):
    """Clock most recent full hour as being spent on this task"""
    if title is None:
        title = 'hours clocked'
    cal_client = get_client()
    content = description + '/n' + ID_STRING_TASK+' '+ \
        ID_STRING_FRONT + task_id + ID_STRING_BACK
    event = gdata.calendar.CalendarEventEntry()
    event.title = atom.Title(text=title)
    event.content = atom.Content(text=content)

    if start_datetime is None:
        # Use current time for the end_time and have the event last 1 hour
        start_time = time.strftime('%Y-%m-%dT%H:00:00.000Z',
            time.gmtime(time.time() - 3600))
        end_time = time.strftime('%Y-%m-%dT%H:00:00.000Z',
            time.gmtime(time.time()))
    elif end_datetime is None:
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
            time.gmtime(
                (start_datetime + datetime.timedelta(0,3600)).timetuple()))
    else:
        start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
            time.gmtime(start_datetime.timetuple()))
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
            time.gmtime(end_datetime.timetuple()))
    event.when.append(gdata.calendar.When(start_time=start_time,
        end_time=end_time))
    new_event = cal_client.InsertEvent(
        event, '/calendar/feeds/default/private/full')
    return new_event

if __name__ == '__main__':
    print get_week_hours(['10', '11', '12'], '2010-07-05', '2010-07-24')
