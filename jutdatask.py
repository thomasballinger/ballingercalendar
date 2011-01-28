# task.py by ThomasBallinger@gmail.com

from copy import deepcopy
import datetime
import abstracttask
import jutdaapi
import time

class Task(abstracttask.Task): # should inherit from base abstract class, which has all att's common to both implementations
    """Represents a task"""
    def __init__(self):
        """Creates a local new task"""
        abstracttask.Task.__init__(self)
        self._ticket_id = ''# this is an implementation detail of jutda task tracker
        self.timespent = datetime.timedelta(0) # not editable permenently, but saves data from hours
        self.starttime = datetime.datetime.now() # ticket creation time in this implementation 
        self.isappointment = False # always false for these
        self.followups = [] # not likely to be used, since other implementation doesn't have it.
        self._orig = None
        self.submitter_email = None

    def __repr__(self):
        """not for general use"""
        return 'jutdatask: '+self.name

    def __cmp__(a,b):
        """a comparison for sorting """
        td = b.duedate - a.duedate
        return td.days * 24*60*60 + td.seconds

    def __eq__(a,b): #Todo: this needs major testing of reading, writing
        """Used for checking for changes between tasks.

        Only tests things that could have changed in the database
        while local edits were being made.
        We should be comparing tickets instead, since the question
        we're trying to answer is 'has the database representation
        changed', but this is more general."""
        if not a.assigner == b.assigner:
            return False
        if not a.description == b.description:
            return False
        if not a.starttime == b.starttime:
            return False
        if not a.followups == b.followups:
            return False
        if not a.id == b.id:
            return False
        if not a._ticket_id == b._ticket_id:
            return False
        if not a.iscompleted == b.iscompleted:
            return False
        if not a.name == b.name:
            return False
        if not a.priority == b.priority:
            return False
        if not a.whose == b.whose:
            return False
        if not a.submitter_email == b.submitter_email:
            return False

    def put(self):
        updateTask(self)

    def _save_state_as_orig(self):
        """Overwrites original with current state"""
        self._orig = None
        self._orig = deepcopy(self)

    def webedit(self):

        webbrowser.open_new_tab()
        raw_input('Hit Enter when done editing task in webbrowser')
        self.refresh_local()

def createTasks():
    """Returns a (hopefully full) list of task objects"""
    tickets = jutdaapi.get_tickets(queues=[3]) # this works better (still not
    # perfect) if list results is set to 1000 in jutda user settings
    tasks = []
    for ticket in tickets:
        tasks.append(createTask(ticket))
    return tasks

def createDetailedTask(ticket_id):
    """Returns"""
    detailed_ticket = jutdaapi.get_detailed_ticket(ticket_id)
    if not detailed_ticket:
        raise ValueError('bad ticket id '+ticket_id)
    return ticketToTask(ticket)

def ticketToTask(ticket):
    task = Task()
    task._ticket_id = ticket.ticket_id
    title = ticket.title
    last_for_index = max(title.rfind('for:'), title.rfind('For:'))
    if last_for_index >= 0:
        assigner = title[last_for_index+4:].title().strip()
    if assigner:
        task.assigner = assigner
        task.name = ticket.title[:last_for_index]
    else:
        task.assigner = 'no one'
    try:
        task.description = ticket.description
        task.followups = ticket.followups
    except AttributeError:
        task.description = None
        task.followups = None
    task.sumbitter_email = ticket.submitter_email
    if not task.submitter_email:
        task.submitter_email = None
    task.id = 't_'+ticket.ticket_id
    task.isappointment = False
    status = ticket.status
    if 'resolved' in status or 'closed' in status:
        task.iscompleted = True
    elif 'open' in status:
        task.iscompleted = False
    else:
        raise ValueError("Bad status read from ticket: "+status)
    task.iscompleted = ticket.status
    task.priority = (ticket.priority - 1) * 2
    task.starttime = ticket.creation_date
    task.timespent = datetime.timedelta(0)
    task.whose = ticket.owner
    if not task.whose:
        task.whose = 'no one'
    task.url = ticket.url
    task._save_state_as_orig()
    return task

def updateTask(task):
    """Updates the database task with local information, perhaps creating a new one"""
    # First check to see if task exists
    detailed_ticket = jutdaapi.get_detailed_ticket(task._ticket_id)
    if not detailed_ticket:
        print 'task does not exist yet'
        return False
    # If so, check that things have actually changed (diff edited and orig)
    database_task = ticketToTask(jutdaapi.get_detailed_ticket(task._ticket_id))
    if task._orig == task:
        return 'no changes to make'
        return False
    # If so, check that no one else has made changes (diff orig and database)
    if not database_task == task._orig:
        print 'task has changed in database'
        return False
    priority = (task.priority + 2) / 2
    if task.assigner != 'no one':
        title = task.title + 'for: '+task.assigner
    else:
        title = task.title
    description = task.description
    return judtaapi.edit_ticket(ticket_id, title=title, queue=None, submitter_email=None,
            description=description, priority=priority)

def deleteTask(task):
    """Deletes the task via the api"""
    return jutdaapi.delete_ticket(task._ticket_id, 'yep, i really want to do this')

def newTask(name, body, assigner, priority=None, submitter_email=None, whose=None):
    """Creates a new ticket in the database too"""
    if whose:
        user_id = jutdaapi.find_user(whose)
        if not user_id:
            raise ValueError('bad whose assignment: '+str(whose))
    title = name + ' for: '+assigner
    priority = (priority + 2) / 2
    ticket_id = jutdaapi.create_ticket(3, title, description,
            priority=priority, submitter_email=submitter_email)
    # Is there a race condition here?  In this kind of database
    # I would assume not.
    time.wait(1)
    t = ticketToTask(jutdaapi.get_detailed_ticket(ticket_id))
    updateTask(t)
    return t

def formatTask(task):
    raise NotImplementedError('some sort of nice text display')
