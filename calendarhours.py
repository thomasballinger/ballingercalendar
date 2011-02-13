# hours.py by ThomasBallinger@gmail.com
"""This module contains methods for dealing with hours worked on tasks,
implemented via the user's main Google calendar."""
import re
import datetime
import time
import abstracttask

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

(EMAIL, PASSWORD) = auth.get_authentication('gmailaddress', 'gmailpassword')
ID_STRING_TASK  = 'qyvztaskqyvz'
ID_STRING_FRONT = 'qyvz'
ID_STRING_BACK  = 'qyvz'

MEETING_ID = 'meeting'

def get_client():
    """Returns a local authenticated client for gdata stuff"""
    # Add a way to get a web-type client
    cal_client = gdata.calendar.service.CalendarService()
    cal_client.email = EMAIL
    cal_client.password = PASSWORD
    cal_client.source = 'ballingercalendar local app'
    cal_client.ProgrammaticLogin()
    return cal_client

class MeetingTask(abstracttask.Task):
    """Task-like object which is only recorded in the hours database"""
    def __init__(self, name, description, length):
        abstracttask.Task.__init__(self)
        self.name = name
        self.description = description
        self.assigner = 'Lab'
        self.timespent = length

    def put(self):
        raise NotImplemented("meeting tasks are read only until I bother to implement edit methods")

    def __repr__(self):
        return '<MeetingTask '+self.name+' '+str(self.timespent)+'>'

def get_hours_worked_on_all_tasks(ds1=None, ds2=None):
    """Returns a dict of task ids as keys, timedeltas as values, and a list of meetingtasks.

    the id 'meeting' may be present in the hours dict."""
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    if not ds1:
        raise Exception('not implemented yet')
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', ID_STRING_TASK)
    query.start_min = ds1
    query.start_max = ds2
    print ds1, ds2
    print 'inclusive, exclusive'
    query.max_results = 1000 # could cause scaling problems for ~> 100 days or so
    cal_client = get_client()
    feed = cal_client.CalendarQuery(query)
    hours_dict = {}
    meeting_tasks = []
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
            print event.title.text, start, end
            print delta
        if task_id in hours_dict:
            hours_dict[task_id] += hours
        else:
            hours_dict[task_id] = hours
        if task_id == 'meeting':
            meeting_tasks.append(MeetingTask(event.title.text, event.content.text, hours))
    return hours_dict, meeting_tasks

def get_hours_worked(ds1=None, ds2=None):
    hours_dict, meetings = get_hours_worked_on_all_tasks(ds1, ds2)
    return sum(hours_dict.values()[1:], hours_dict.values()[0])

def get_meeting_objects(ds1=None, ds2=None):
    return get_hours_worked_on_all_tasks(ds1, ds2)[1]


def test_search(text):
    """Searches for text in all events in calendar"""
    cal_client = get_client()
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', text)
    query.max_results = 1000 # could cause scaling problems for ~> 100 days or so
    feed = cal_client.CalendarQuery(query)
    for event in feed.entry:
        print event.title.text

def get_hours_worked_on_single_task(task_id, ds1=None, ds2=None):
    """Returns just a timedelta for hours worked in a time period or ever on a task"""
    if bool(ds1) ^ bool(ds2):
        raise Exception('use both or neither datetime arguments')
    idstring = ID_STRING_TASK + ' ' + ID_STRING_FRONT + task_id + ID_STRING_BACK
    cal_client = get_client()
    query = gdata.calendar.service.CalendarEventQuery(
        'default', 'private', 'full', idstring)
    if ds1:
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

def clock_meeting_time(title, description=''):
    """Clocks more recent full hour as being spent on this meeting"""
    clock_time(MEETING_ID, title=title, description=description)

def clock_time(task_id, title=None, description='',
         start_datetime=None, end_datetime=None):
    """Clocks most recent full hour as being spent on this task"""
    if title is None:
        title = 'hours clocked'
    cal_client = get_client()
    content = description + '\n ' + ID_STRING_TASK+' '+ \
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

def fix_all_descriptions():
    cal_client = get_client()
    events = DateRangeQuery(cal_client)
    raw_input()
    for event in events:
        if event.content.text and '/nqyvztaskqyvz' in event.content.text:
            FixDescription(cal_client, event)
        elif event.content.text == None:
            print event.title.text, 'event has no description'
        else:
            print event.title.text, 'event is fine'

def DateRangeQuery(calendar_service, start_date='2010-06-01', end_date='2011-03-01'):
    print 'Date range query for events on Primary Calendar: %s to %s' % (start_date, end_date,)
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full')
    query.start_min = start_date
    query.start_max = end_date
    query.max_results=1000
    feed = calendar_service.CalendarQuery(query)
    for i, an_event in enumerate(feed.entry):
        print '\t%s. %s' % (i, an_event.title.text,)
        for a_when in an_event.when:
            print '\t\tStart time: %s' % (a_when.start_time,)
            print '\t\tEnd time:   %s' % (a_when.end_time,)
    return feed.entry

def FixDescription(calendar_service, event):
    previous_desc = event.content.text
    event.content.text = re.sub("/nqyvztaskqyvz", "\n qyvztaskqyvz", previous_desc)
    print 'Updating desc of event '+event.title.text
    return calendar_service.UpdateEvent(event.GetEditLink().href, event)

if __name__ == '__main__':
    #fix_all_descriptions()
    #print get_hours_worked_on_tasks(['10', '11', '12'], '2010-07-05', '2010-07-24')
    #print test_search('qyvztaskqyvz')
    #import pudb; pudb.set_trace()
    print get_hours_worked_on_all_tasks('2011-01-01', '2011-02-12')
    print get_hours_worked_on_all_tasks('2010-07-05', '2010-07-24')
    print get_hours_worked('2010-11-28', '2010-12-04')
