# task.py by ThomasBallinger@gmail.com

from copy import deepcopy
import datetime
import abstracttask
import jutdaapi
import time
import re
import webbrowser

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
        if not a.assigner.title() == b.assigner.title():
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
        return True

    def put(self):
        updateTask(self)

    def _save_state_as_orig(self):
        """Overwrites original with current state"""
        self._orig = None
        self._orig = deepcopy(self)

    def webedit(self):
        webbrowser.open_new_tab(jutdaapi.SERVER+self.url+'edit/')

def createTasks():
    """Returns a (hopefully full) list of task objects"""
    tickets = jutdaapi.get_tickets(queues=[3]) # this works better (still not
    # perfect) if list results is set to 1000 in jutda user settings
    tasks = []
    for ticket in tickets:
        tasks.append(ticketToTask(ticket))
    return tasks

def detailedVersion(task):
    return createDetailedTask(task.ticket_id)

def createDetailedTask(ticket_id):
    """Returns"""
    detailed_ticket = jutdaapi.get_detailed_ticket(ticket_id)
    if not detailed_ticket:
        raise ValueError('bad ticket id '+ticket_id)
    return ticketToTask(detailed_ticket)

def ticketToTask(ticket):
    task = Task()
    task._ticket_id = ticket.ticket_id

    # old version
    #title = ticket.title
    #last_for_index = max(title.rfind('for:'), title.rfind('For:'))
    #task.assigner = 'no one'
    #try:
    #    _ = ticket.description
    #    if not 'tasktrackermeta id' in ticket.description:
    #        task.id = 't_'+str(ticket.ticket_id)
    #except AttributeError:
    #    pass
    #assigner = None
    #if last_for_index >= 0:
    #    assigner = title[last_for_index+4:].title().strip()
    #if assigner:
    #    #instead we use custom html tag for this
    #    task.assigner = assigner
    #    task.name = ticket.title[:last_for_index]
    #else:
    #    task.name = ticket.title

    title = ticket.title
    assigner_match = re.match(r"\((.*?)\) .*", title)
    if assigner_match:
        task.assigner = assigner_match.group(1).title()
        task.name = re.sub(r"\(.*?\) ", "", title)
    else:
        task.name = title

    try:
        task.description = ticket.description

        id_match = re.search(r'&lt;tasktrackermeta id=&quot;(.*?)&quot;/&gt;', ticket.description)

        # this doesn't work because it's not html, it's escaped html
        #task.description = re.sub('<tasktrackermeta .*?/>', '', ticket.description)

        # We're not using this because it's so ugly while the html is escaped, since
        # we've got another option
        #assigner_match = re.search(r'<tasktrackermeta assigner="(.*?)"/>', ticket.description)
        #id_match = re.search(r'<tasktrackermeta id="(.*?)"/>', ticket.description)
        task.description = re.sub(r'&lt;tasktrackermeta id=&quot;(.*?)&quot;/&gt;', '', ticket.description)
        if id_match:
            task.id = id_match.group(1)
        #if assigner_match:
        #    task.assigner = assigner_match.group(1).title()
    except AttributeError:
        task.description = None
    try:
        task.followups = ticket.followups
    except AttributeError:
        task.followups = None
    try:
        task.submitter_email = ticket.submitter_email
    except AttributeError:
        task.submitter_emial = ''
    if not task.submitter_email:
        task.submitter_email = None
    task.isappointment = False
    status = ticket.status
    if 'resolved' in status or 'closed' in status:
        task.iscompleted = True
    elif 'open' in status:
        task.iscompleted = False
    else:
        raise ValueError("Bad status read from ticket: "+status)
    #task.priority = (ticket.priority - 1) * 2
    task.priority = ticket.priority
    task.starttime = ticket.creation_date
    task.timespent = datetime.timedelta(0)
    task.whose = ticket.owner
    if not task.whose or task.whose == 'Unassigned':
        task.whose = 'no one'
    task.url = ticket.url
    task._save_state_as_orig()
    return task

def updateTask(task):
    """Updates the database task with local information, perhaps creating a new one.
    Returns true if the database succesfully reflects the local one."""
    # First check to see if task exists
    detailed_ticket = jutdaapi.get_detailed_ticket(task._ticket_id)
    if not detailed_ticket:
        print 'task does not exist yet'
        return False
    # If so, check that things have actually changed (diff edited and orig)
    database_task = ticketToTask(detailed_ticket)
    if task._orig == task:
        return 'no changes to make'
        return True
    # If so, check that no one else has made changes (diff orig and database)
    if not database_task == task._orig:
        print 'task has changed in database; refresh task!'
        return False
    #priority = (task.priority + 2) / 2
    priority = task.priority
    if task.assigner not in  ['no one', 'Unassigned']:
        title = '('+task.assigner.title()+') '+task.name
        #if task.name[-1] == ' ':
        #    title = task.name + 'for: '+task.assigner.title()
        #else:
        #    title = task.name + ' for: '+task.assigner.title()
    else:
        title = task.name
    description = task.description
    #if task.assigner != 'no one':
    #    description += '<tasktrackermeta assigner="'+task.assigner+'"/>'
    if 't' not in task.id:
        description += '<tasktrackermeta id="'+task.id+'"/>'
    return jutdaapi.edit_ticket(task._ticket_id, title=title, queue=None, submitter_email=None,
            description=description, priority=priority)

def deleteTask(task):
    """Deletes the task via the api"""
    return jutdaapi.delete_ticket(task._ticket_id, 'yep, i really want to do this')

def newTask(name, description, assigner, id=None, priority=None, submitter_email=None, whose=None):
    """Creates a new ticket in the database too, return Ticket"""
    if whose:
        user_id = jutdaapi.find_user(whose)
        if not user_id:
            raise ValueError('bad whose assignment: '+str(whose))
    #title = name + ' for: '+assigner.title()
    # that was the old scheme
    title = '('+assigner.title()+') '+name

    if priority != None:
        #priority = (int(priority) + 2) / 2
        priority = int(priority)
    RA_queue = 3
    #if assigner != 'no one':
    #    description += '<tasktrackermeta assigner="'+assigner+'"/>'
    if isinstance(id, str):
        description += '<tasktrackermeta id="'+id+'"/>'
    ticket_id = jutdaapi.create_ticket(RA_queue, title, description,
            priority=priority, submitter_email=submitter_email)
    # Is there a race condition here?  In this kind of database
    # I would assume not.
    time.sleep(1)
    ticket = jutdaapi.get_detailed_ticket(ticket_id)
    t = ticketToTask(ticket)
    return t

def formatTask(task):
    raise NotImplementedError('some sort of nice text display')

if __name__ == '__main__':
    import pudb; pudb.set_trace()
    task = newTask('tomTestTask', "this is a task to test tom's jutda task api\n linebreaks included.",
            'Taskassigner')
    from pprint import pprint
    print('newtask:')
    print task
    print task.description
    raw_input('')
    print updateTask(task)
    task.name = 'newnameof this task'
    print updateTask(task)
    raw_input('hit return to delete the task')
    deleteTask(task)
