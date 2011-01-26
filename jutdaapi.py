# jutdaapi.py by ThomasBallinger@gmail.com
"""For remotely interacting with an instance of Judta-Helpdesk"""

import webbrowser
import re
import datetime
import urllib2
import urllib
import auth
import json
from dateutil import parser as dateutilparser

USER = 'tomb'
SERVER = 'http://pnl-t75-1.bwh.harvard.edu:9000'
def getPassword():
    user, password = auth.get_authentication()
    return password

class JutdaSession():
    """Keeps track of authentication data for screen scrapings"""
    sort_choices = ['create', 'status', 'queue', 'title', 'priority', 'assigned_to']
    status_dict = {'open' : 1, 'reopened' : 2, 'resolved' : 3, 'closed' : 4}
    def __init__(self):
        # build opener with HTTPCookieProcessor
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        urllib2.install_opener(self.opener)

        f = self.opener.open(SERVER+'/login/')
        s = f.read()
        match = re.search(r"<input type='hidden' name='(csrfmiddlewaretoken)' value='([0-9a-z]+)' />", s)
        (csrfmiddleware, value) =  match.group(1), match.group(2)

        # jutda helpdesk expects 'usersname' and 'password' as query params,
        # and a 'CSRFMiddlewareToken'
        datadict = {'username': USER, 'password': getPassword()}
        datadict[csrfmiddleware] = value
        p = urllib.urlencode(datadict)

        # perform login with params
        f = self.opener.open(SERVER+'/login/', p)
        data = f.read()
        f.close()

        # any requests after this should automatically pass back any cookies receied
        # during login... thanks to the HTTPCookieProcessor

    def get_tickets(self, sort=None, sortreverse=False, owners=[], statuses=[], queues=[], keyword='', with_browser=False):
        """Returns all tickets, with optional query parameters.

        sort: created, title, queue, status, priority, owner
        owners: list of owner ids
        statuses: list of ['open', 'reopened', 'resolved']
        queues: list of queue ids
        keywords: list of words

        """
        # input sanitization
        if sort and sort not in JutdaSession.sort_choices:
            raise ValueError("Bad sort choice")
        try:
            [int(owner) for owner in owners]
        except ValueError:
            owners = [find_user(owner) for owner in owners]
            if False in owners:
                raise ValueError("Bad users choice: found False in "+users)
        for status in statuses[:]:
            if status in status_dict.values():
                pass
            elif status in status_dict.keys():
                statuses.remove(status)
                statuses.append(status_dict[status])
            else:
                raise ValueError("Bad status choice: "+status)
        try:
            [int(queue) for queue in queues]
        except ValueError:
            queues = [find_queue(queue) for queue in queues]
            if False in queues:
                raise ValueError("Bad queue choice: found False in "+queues)

        # contructing get request
        datadict = ()
        if sort:
            datadict += (('sort', sort),)
        if sortreverse:
            datadict += (('sortreverse', 'on'),)
        for owner in owners:
            datadict += (('assigned_to', owner),)
        for queue in queues:
            datadict += (('queue', queue),)
        for status in statuses:
            datadict += (('status', status),)
        if keyword:
            datadict += (('q', keyword),)
        data = urllib.urlencode(datadict)
        if with_browser:
            webbrowser.open_new_tab(SERVER+"/tickets/?"+ data)
            return True
        f = self.opener.open(SERVER+"/tickets/?"+ data)
        s = f.read()
        f.close()

        regexcode = (r"<tr class='row_\w+ row_hover'>\s*" +
                r"<th>(.*)</th>\s*" +
                r"<td>(.*)</td>\s*" +
                r"<td>(.*)</td>\s*" +
                r"<th>(.*)</th>\s*" +
                r"<td>(.*)</td>\s*" +
                r"<td>(.*)</td>\s*" +
                r"<td>(.*)</td>\s*" +
                r"<td>(.*)</td>\s*" +
                r"</tr>"
               r"")
        screenscrapes = re.findall(regexcode, s)
        tickets = [JutdaTicket(scrape) for scrape in screenscrapes]
        return tickets
def get_tickets(**argsdict):
    """Convenience function for JutdaSession().get_tickets()"""
    return JutdaSession().get_tickets(**argsdict)
class JutdaTicket():
    """Represents a task from the Jutda Helpdesk"""
    def __init__(self, screenscrape):
        (number, _, priority, title, queue, status, created, owner) = screenscrape
        ((self.url, self.title,),) = re.findall(r"<a\s*href='(\S+)'>(.+)</a>", title)
        self.owner = owner
        self.queue = queue
        self.status = status
        self.create_date = dateutilparser.parse(re.findall(r"<span title='(.*)'>.*</span>", created)[0])
        self.priority = int(re.findall(r"<span class='.*'>(\d)</span>", priority)[0])
        self.ticket_id = int(re.findall(r"<a href='\S+'>\[.*-(\d+)\]</a>", number)[0])

    def __repr__(self):
        return '<'+' '.join([self.title, self.owner, str(self.ticket_id), self.url])+'>'

    def __cmp__(self, other):
        return self.priority - other.priority

    def edit_in_browser(self):
        webbrowser.open_new_tab(SERVER+self.url)

def find_queue(queue):
    """Helper method to return int id of queue"""
    queue_dict = list_queues()
    if queue in queue_dict:
        return queue_dict[queue]
    else:
        return False

# the methods below use the jutdahelpdesk api very directly
def create_ticket(queue, title, body, submitter_email=None, assigned_to=None, priority=None):
    """Returns the ID of a newly created task"""
    datadict = {"queue" : queue, "body" : body, "title" : title, "user" : USER, "password" : getPassword()}
    if submitter_email:
        datadict["submitter_email"] = submitter_email
    if assigned_to:
        datadict["assigned_to"] = assigned_to
    if priority:
        datadict["priority"] = priority
    data = urllib.urlencode(datadict)
    f = urllib2.urlopen(SERVER+"/api/create_ticket/", data)
    s = f.read()
    f.close()
    return int(s)

def delete_ticket(ticket_id, confirm):
    """Entirely deletes a ticket"""
    datadict = {"ticket" : ticket_id, "confirm" : confirm, 'user' : USER, 'password' : getPassword()}
    data = urllib.urlencode(datadict)
    f = urllib2.urlopen(SERVER+"/api/delete_ticket/", data)
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    return True

def hold_ticket(ticket_id):
    """Places a ticket on hold, preventing it from being escalated"""
    raise NotImplemented("I don't think we use this functionality")

def unhold_ticket(ticket_id):
    """Removes a ticket from hold"""
    raise NotImplemented("I don't think we use this functionality")

def add_followup(ticket_id, message, public=None):
    """Adds a followup """
    datadict = {"ticket" : ticket_id,  "message" : message, "user" : USER, "password" : getPassword()}
    if public:
        datadict["public"] = public
    data = urllib.urlencode(datadict)
    f = urllib2.urlopen(SERVER+"/api/add_followup/", data)
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    return True

def resolve(ticket_id, resolution):
    datadict = {"ticket" : ticket, "resolution" : resolution}
    data = urllib.urlencode(datadict)
    f = urllib2.urlopen(SERVER+"/api/resolve/", data)
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    return True

def list_queues():
    """Returns a dictionary of queue IDs, with names as keys"""
    data = urllib.urlencode({"user" : USER, "password" : getPassword()})
    f = urllib2.urlopen(SERVER+"/api/list_queues/", data)
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    d = json.loads(s)
    queues = {}
    for queue in d:
        queues[queue["title"]] = queue["id"]
    return queues

def find_user(user):
    """Returns an a integer id that is the user's Task Tracker ID"""
    query = user
    data = urllib.urlencode({"username" : query, "user" : USER, "password" : getPassword()})
    try:
        f = urllib2.urlopen(SERVER+"/api/find_user/", data)
    except urllib2.HTTPError:
        return False
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    return int(s)

if __name__ == '__main__':
    #import pudb; pudb.set_trace()
    print find_user('tomb')
    print find_user('fred')
    print list_queues()
    newticket = create_ticket(u'3', 'Test task1 by tom for: Ryan', 'test text')
    print newticket
    print delete_ticket(newticket, 'yes, really')
    pass
    from pprint import pprint
    #pprint(session.get_tickets())
    pprint(get_tickets(sort='title', sortreverse='on', queues=['3']))
