# jutdaapi.py by ThomasBallinger@gmail.com
"""For remotely interacting with an instance of Judta-Helpdesk"""

import webbrowser
import re
import urllib2
import urllib
import auth
import json
from dateutil import parser as dateutilparser

USER, PASSWORD = auth.get_authentication('pnluser', 'pnlpassword')
SERVER = 'http://pnl-t75-1.bwh.harvard.edu:9000'

class JutdaSession():
    """Keeps track of authentication data for screen scrapings"""
    sort_choices = ['created', 'status', 'queue', 'title', 'priority', 'assigned_to']
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
        datadict = {'username': USER, 'password': PASSWORD}
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
        statuses: list of ['open', 'reopened', 'resolved', 'closed']
        queues: list of queue ids
        keywords: space separated string of words

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
            if status in JutdaSession.status_dict.values():
                pass
            elif status in JutdaSession.status_dict.keys():
                statuses.remove(status)
                statuses.append(JutdaSession.status_dict[status])
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
        if re.search(r"<h2>Login</h2>", s):
            raise Exception("Login Failed")

        # TODO: move this to JutdaTicket code class method?
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
        tickets = [JutdaTicket(tablescreenscrape=scrape) for scrape in screenscrapes]
        return tickets

    def get_detailed_ticket(self, ticket_id):
        """Gets a ticket with description and followup information"""
        try:
            f = self.opener.open(SERVER+"/tickets/"+str(ticket_id))
        except urllib2.HTTPError:
            return False
        s = f.read()
        ticket = JutdaTicket(detailscreenscrape=s)
        return ticket

    def edit_ticket(self, ticket_id, title=None, queue=None, submitter_email=None, description=None, priority=None,
            append_to_title=None, append_to_description=None):
        """Edits a ticket."""
        # first, sanitize data
        ticket_id = int(ticket_id)
        if priority:
            priority = int(priority)

        # next, learn the current status of the ticket
        ticket = self.get_detailed_ticket(ticket_id)
        if title:
            ticket.title = title
        if queue:
            ticket.queue = queue
        if submitter_email:
            ticket.submitter_email = submitter_email
        if description:
            ticket.description = description
        if priority:
            ticket.priority = priority
        if append_to_title:
            ticket.title += append_to_title
        if append_to_description:
            ticket.description += append_to_description
        datadict = {
                'title': ticket.title,
                'queue': ticket.queue,
                'submitter_email' : ticket.submitter_email,
                'description' : ticket.description,
                'priority' : ticket.priority}
        data = urllib.urlencode(datadict)
        f = self.opener.open(SERVER+"/tickets/"+str(ticket.ticket_id)+"/edit/", data)
        s = f.read()
        return True

def get_tickets(**argsdict):
    """Convenience function for JutdaSession().get_tickets()"""
    return JutdaSession().get_tickets(**argsdict)

def edit_ticket(*args, **argsdict):
    """Convenience function for JutdaSession().edit_ticket()"""
    return JutdaSession().edit_ticket(*args, **argsdict)

def get_detailed_ticket(ticket_id):
    """Convenience function for JutdaSession().get_detailed_ticket()"""
    return JutdaSession().get_detailed_ticket(ticket_id)

class JutdaTicket(object):
    """Represents a ticket from the Jutda Helpdesk"""
    def __init__(self, tablescreenscrape=None, detailscreenscrape=None):
        if not (tablescreenscrape or detailscreenscrape):
            raise ValueError("need information about the ticket from the server")
        if tablescreenscrape:
            (number, _, priority, title, queue, status, created, owner) = tablescreenscrape
            ((self.url, self.title,),) = re.findall(r"<a\s*href='(\S+)'>(.+)</a>", title)
            self.title = re.sub(r"<br\s*/>", r"\n", self.title)
            self.title = re.sub(r"&#39;", r"'", self.title)
            self.owner = owner
            self.queue = queue
            self.status = status.lower()
            if not self.status in JutdaSession.status_dict:
                raise Exception('Bad status scraped: '+self.status+' not in '+str(JutdaSession.status_dict))
            self.creation_date = dateutilparser.parse(re.findall(r"<span title='(.*)'>.*</span>", created)[0])
            self.priority = int(re.findall(r"<span class='.*'>(\d)</span>", priority)[0])
            self.ticket_id = int(re.findall(r"<a href='\S+'>\[.*-(\d+)\]</a>", number)[0])
        elif detailscreenscrape:
            s = detailscreenscrape
            followups = re.findall(r"<div class='followup'>\s*<div class='title'>(.*)<span class='byline'>by (.*) " +
                                   r"<span title='(.*)'>.*ago</span>.*</span></div>\s*(.*)\s+</div>", s)
            self.followups = []
            for followup in followups:
                what, whom, when, body = followup
                f = {}
                f['action'] = what
                f['whom'] = whom
                f['when'] = dateutilparser.parse(when)
                f['body'] = body
                self.followups.append(f)
            self.ticket_id = int(re.findall(r"href='/tickets/(\d+)/edit/", s)[0])
            self.creation_date = dateutilparser.parse(re.findall(r"<th>Submitted On</th>\s*<td>(.*)\(.*</td>", s)[0])
            self.priority = int(re.findall(r"<th>Priority</th>\s*<td>(\d)\.\s*", s)[0])
            self.copies_to = re.findall(r"<th>Copies To</th>\s*<td>([^<>]*)<", s)[0]
            self.description = re.findall(r"<th colspan='2'>Description</th>\s*</tr>\s*<tr class='[^<>]+'>\s*<td colspan='2'>(.+?)</td>", s, re.DOTALL)[0]

            self.description = re.sub(r"<br\s*/>", r"\n", self.description)
            self.description = re.sub(r"&#39;", r"'", self.description)

            self.title = re.findall(r"<dd><input type='text' name='title' value='(.*)' /></dd>", s)[0]
            self.title = re.sub(r"<br\s*/>", r"\n", self.title)
            self.title = re.sub(r"&#39;", r"'", self.title)
            self.queue = find_queue(re.findall(r"<tr class='row_columnheads'><th colspan='2'>Queue: (.*)</th></tr>", s)[0])
            self.submitter_email = re.findall(r"<th>Submitter E-Mail</th>\s*<td>(.*)</td>", s)[0]
            self.url = "/tickets/"+str(self.ticket_id)
            if re.search(r"<input type='radio' name='new_status' value='1' id='st_open' checked='checked'>", s):
                self.status='open'
            if re.search(r"<input type='radio' name='new_status' value='2' id='st_reopened' checked='checked'>", s):
                self.status='reopened'
            elif re.search(r"<input type='radio' name='new_status' value='3' id='st_resolved' checked='checked'>", s):
                self.status='resolved'
            elif re.search(r"<input type='radio' name='new_status' value='4' id='st_closed' checked='checked'>", s):
                self.status='closed'

            if not self.status in JutdaSession.status_dict:
                raise('Bad status scraped: '+status+' not in '+str(JutdaSession.status_dict))
            # may be unassigned
            self.owner = re.findall(r"<th>Assigned To</th>\s+<td>([^<>]+)<", s)[0].strip()
            if 'Unassigned' in self.owner:
                self.owner = False

            # not always there
            self.resolution = None

    def display(self):
        for att in [att for att in self.__dict__ if (not att.startswith('_') and not callable(self.__dict__[att]))]:
            print att, self.__getattribute__(att)

    def __repr__(self):
        if self.owner:
            owner = self.owner
        else:
            owner = 'unassigned'
        return '<'+' '.join([self.title, owner, str(self.ticket_id), self.url])+'>'

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
    datadict = {"queue" : queue, "body" : body, "title" : title, "user" : USER, "password" : PASSWORD}
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
    datadict = {"ticket" : ticket_id, "confirm" : confirm, 'user' : USER, 'password' : PASSWORD}
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
    datadict = {"ticket" : ticket_id,  "message" : message, "user" : USER, "password" : PASSWORD}
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
    data = urllib.urlencode({"user" : USER, "password" : PASSWORD})
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
    data = urllib.urlencode({"username" : query, "user" : USER, "password" : PASSWORD})
    try:
        f = urllib2.urlopen(SERVER+"/api/find_user/", data)
    except urllib2.HTTPError:
        return False
    s = f.read()
    if f.code != 200:
        return False
    f.close()
    return int(s)

def testAll():
    testReadAndEdit()
    testQueries()

def testReadAndEdit():
    """These tests are specific to the PNL Task Tracker - skip them if you aren't there."""
    print 'running tests...'
    assert find_user('tomb') == 12
    assert not find_user('fred')
    assert list_queues() == {u'INTRuST NLC': u'2', u'PNL RA': u'3'}
    newticket_id = create_ticket(3, 'Jutdaapi test ticket', 'original test ticket descripion')
    print 'newly created ticket has id:', newticket_id
    try:
        newticket = get_detailed_ticket(newticket_id)
        assert newticket
        print 'testing editing ticket title...'
        edit_ticket(newticket_id, title='newtitle')
        assert get_detailed_ticket(newticket_id).title == 'newtitle'
        print 'testing editing ticket queue...'
        edit_ticket(newticket_id, queue=2)
        assert get_detailed_ticket(newticket_id).queue == u'2'
        print 'testing editing ticket submitter_email...'
        edit_ticket(newticket_id, submitter_email='thomasballinger@gmail.com')
        assert get_detailed_ticket(newticket_id).submitter_email == 'thomasballinger@gmail.com'
        print 'testing editing ticket description...'
        edit_ticket(newticket_id, description='this is the new test ticket description')
        assert get_detailed_ticket(newticket_id).description == u'this is the new test ticket description'
        print 'testing editing ticket priority...'
        edit_ticket(newticket_id, priority=5)
        assert get_detailed_ticket(newticket_id).priority == 5
    finally:
        print 'running test cleanup'
        print 'deleting ticket...', delete_ticket(newticket_id, 'yeah')
    assert not get_detailed_ticket(newticket_id)
    phoenix_ticket_id = create_ticket(3, 'another test ticket', 'should have same id as one previously created')
    print 'deleting ticket...', delete_ticket(newticket_id, 'yeah')
    assert newticket_id == phoenix_ticket_id
    print 'all read and editing tests passed'
    return True

def testQueries():
    print 'querying tickets...'
    print 'default', get_tickets(); raw_input()
    print 'sort by created', get_tickets(sort='created'); raw_input()
    print 'sort by title', get_tickets(sort='title', sortreverse=True); raw_input()
    print 'sort by queue', get_tickets(sort='queue'); raw_input()
    print 'sort by priority', get_tickets(sort='priority'); raw_input()
    print 'sort by owner', get_tickets(sort='priority'); raw_input()
    print 'sort by priority', get_tickets(sort='priority'); raw_input()
    print 'get by owner id', get_tickets(owners=[4, 5]); raw_input()
    print 'get by status', get_tickets(statuses=['reopened', 'resolved']); raw_input()
    print 'get by queue', get_tickets(queues=[3]); raw_input()
    print 'get by keyword', get_tickets(keyword='fa fix'); raw_input()
    print 'get by keyword in browser', get_tickets(keyword='fa fix', with_browser=True); raw_input()
    sort_choices = ['created', 'status', 'queue', 'title', 'priority', 'assigned_to']

if __name__ == '__main__':
    #print get_tickets(statuses=['closed'])
    #ticket = get_detailed_ticket(148)
    #print ticket
    #desc = ticket.description
    #print desc
    #testAll()
    #ticket = get_detailed_ticket(100)
    #ticket.display()
    #testAll()

    testReadAndEdit()
    testQueries()
