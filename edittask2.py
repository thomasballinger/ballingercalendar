#!/usr/bin/python
# edittask
# being updated for use with spreadsheet-based tasks
# thomasballinger@gmail.com
import time
import os, sys, optparse
import datetime, parse
import gssltask
import jutdatask
import jutdatask as task
import calendarhours as hours
import cmd
import pretty
from pprint import pprint
import auth
(FULLPNLNAME,) = auth.get_authentication('fullpnlname')

class EditTasksCLI(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ':) '
        self.selected_task = None
        self.updateLocalTasklist()

    def do_updateLocalTasklist(self, arg):
        """Updates the local task list from the database tasks.

        The local list of tasks is automatically updated after most commands,
        but this command causes an immediate update."""
        self.updateLocalTasklist()

    def updateLocalTasklist(self, select_task=None):
        if self.selected_task and not select_task:
            id = self.selected_task.id[:]
        elif select_task:
            id = select_task.id[:]
        else:
            id = None
        self.selected_task = None
        self.task_list = jutdatask.createTasks()
        if id:
            desired_task = [x for x in self.task_list if x.id == id]
        if id and len(desired_task) == 1:
            self.selected_task = desired_task[0]
            self.task_list.remove(self.selected_task)
            self.selected_task = jutdatask.createDetailedTask(self.selected_task._ticket_id)
        else:
            self.selected_task = None

    def do_webEdit(self, arg):
        """Opens a webpage allowing edits of the task at a closer level to the database."""
        if not self.selected_task: print('choose a task first'); return
        self.selected_task.webedit()
        raw_input('Hit Enter when done editing task in webbrowser')
        self.updateLocalTasklist()


    def do_exit(self, arg):
        """Exits this client program."""
        sys.exit(0)

    def do_quit(self, arg):
        sys.exit(0)

    def do_EOF(self, arg):
        print('')
        return True

    def do_getHoursWorked(self, arg):
        if not arg: return False
        print hours.get_hours_worked(arg[:len(arg)/2].strip(), arg[len(arg)/2:].strip())

    def do_getHoursWorkedOnTasks(self, arg):
        if not arg: return False
        hours_dict, meetings = hours.get_hours_worked_on_all_tasks(arg[:len(arg)/2].strip(), arg[len(arg)/2:].strip())
        print self.timedeltaToHoursString(sum(hours_dict.values()[1:], hours_dict.values()[0]))

    def do_prettyHours(self, arg):
        #raise Exception("pretty needs to be more modular to allow jutdatasks")
        #raise Exception("pretty needs to allow hardcoded meetings (move meeting constants to hours)")
        if not arg:
            return False
        splitargs = arg.split()
        (ds1, ds2) = splitargs[:2]
        if len(splitargs) == 3:
            filename = splitargs[2]
            return pretty.showWeekly(ds1, ds2, filename=filename)
        return pretty.showWeekly(ds1, ds2)

    def do_task(self, arg):
        if arg:
            l = [x for x in self.task_list if x.name == arg]
            if not l:
                l = [x for x in self.task_list if x.name.replace('-','_').replace("'",'').replace(' ','_').lower() == arg.lower()]
                if not l:
                    print('no such task')
                    return
            self.selected_task = l[0]
            self.task_list.remove(self.selected_task)
            self.selected_task = jutdatask.createDetailedTask(self.selected_task._ticket_id)
            self.task_list.append(self.selected_task)
            print(self.selected_task)
        elif self.selected_task:
            print(self.selected_task)
        else:
            print('select a task, or create a new one')

    def complete_task(self, text, line, beginindex, endindex):
        if not text:
            a = [x.name.replace(' ','_').replace('-','_').replace("'",'') for x in self.task_list]
            return a
        else:
            a = [x.name.replace(' ','_').replace('-','_').replace("'",'') for x in [t for t in self.task_list if text.lower() in t.name.replace(' ','_').replace("'",'').lower()]]
            return a

    def do_rename(self,arg):
        if not self.selected_task: print('choose a task first'); return
        self.selected_task.name = arg.replace('_',' ')
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_newtask(self,arg):
        name = raw_input('task name:')
        description = raw_input('task description:')
        assigner = raw_input('task assigner:')
        priority = raw_input('priority:')
        submitter_email = raw_input('submitter email:')
        whose = raw_input('whose')
        customID = None
        if not priority:
            priority = None
        if not submitter_email:
            submitter_email = None
        if not whose:
            whose = None
        if not all([name, description, assigner]):
            print('nm')
            return False
        t = task.newTask(name, description, assigner, customID, priority, submitter_email, whose)
        self.updateLocalTasklist(t)

    def do_customIdNewtask(self,arg):
        customID = raw_input('custom_id')
        name = raw_input('task name:')
        description = raw_input('task description:')
        assigner = raw_input('task assigner:')
        priority = raw_input('priority:')
        submitter_email = raw_input('submitter email:')
        whose = raw_input('whose')
        if not priority:
            priority = None
        if not submitter_email:
            submitter_email = None
        if not whose:
            whose = None
        if not all([name, description, assigner]):
            print('nm')
            return False
        t = task.newTask(name, description, assigner, customID, priority, submitter_email, whose)
        self.updateLocalTasklist(t)

    def do_description(self, arg):
        if not self.selected_task: print('choose a task first'); return
        if not arg:
            print('description:'+self.selected_task.description)
            return
        self.selected_task.description = arg
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_assigner(self, arg):
        if not self.selected_task: print('choose a task first'); return
        if not arg:
            print 'assigner:',self.selected_task.assigner
            return
        self.selected_task.assigner = arg
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_whose(self, arg):
        raise Exception('Tickets do not save this information, so it cannot we saved')
        import pudb; pudb.set_trace()
        if not self.selected_task: print('choose a task first'); return
        if not arg:
            print 'whose:',self.selected_task.whose
            return
        self.selected_task.whose = arg
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_priority(self, arg):
        if not self.selected_task: print('choose a task first'); return
        if not arg:
            print 'priority:',self.selected_task.priority
            return
        if not -1<int(arg)<10:
            print('bad priority value')
            return
        self.selected_task.priority = int(arg)
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_notComplete(self, arg):
        if not self.selected_task: print('choose a task first'); return
        self.selected_task.iscompleted= False
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_complete(self, arg):
        if not self.selected_task: print('choose a task first'); return
        self.selected_task.iscompleted= True
        self.selected_task.put()
        self.updateLocalTasklist()

    def do_showCurrentTask(self, arg):
        if not self.selected_task: print 'select a task first'; return
        t = self.selected_task
        print(t.name)
        for (label,prop) in zip(
        ['desc:','assigned by:','priority:','time spent','start time','is complete:', 'id'],
        [t.description, t.assigner, t.priority, t.timespent, t.starttime, t.iscompleted, t.id]):
            if prop:
                print label,prop
        print t.id

    def do_removeTask(self, arg):
        if not self.selected_task: print 'select a task first'; return
        check = parse.parseBoolean(raw_input('really delete task'+self.selected_task.__repr__()+'?\n'))
        if check:
            result = task.deleteTask(self.selected_task)
            self.selected_task = None
            print result
            if result:
                print 'task deleted'
            else:
                print 'ERROR: Task NOT deleted'
        else:
            print 'deletion canceled'
        self.updateLocalTasklist()

    def do_listCompleted(self, arg):
        pprint([t for t in self.task_list if t.iscompleted])

    def do_listIncomplete(self, arg):
        task_list = [t for t in self.task_list if not t.iscompleted]
        if not task_list:
            print None
            return
        task_list.sort(key=lambda t: t.priority)
        maxTaskLength = max(len(t.name) for t in task_list)
        for t in task_list:
            if t.iscompleted:
                status = 'Complete'
            else:
                status = 'Open    '
            print str(t.priority)+'\t'+status+'\t'+(t.name + ' '*maxTaskLength)[:maxTaskLength]+'\t'+t.assigner+'\t'+str(t.whose)
            #print '\t'+str(t.description)+'\n'

    def do_listOpen(self, arg):
        task_list = [t for t in self.task_list if t.whose == 'no one' and not t.iscompleted]
        if not task_list:
            print None
            return
        task_list.sort(key=lambda t: t.priority)
        maxTaskLength = max(len(t.name) for t in task_list)
        for t in task_list:
            if t.iscompleted:
                status = 'Complete'
            else:
                status = 'Open    '
            print str(t.priority)+'\t'+status+'\t'+(t.name + ' '*maxTaskLength)[:maxTaskLength]+'\t'+t.assigner
            print '\t'+str(t.description)+'\n'

    def do_listMyProjects(self, arg):
        if arg:
            task_list = [t for t in self.task_list if not t.iscompleted and t.whose.lower()==arg.lower()]
        else:
            task_list = [t for t in self.task_list if not t.iscompleted and t.whose.lower()==FULLPNLNAME.lower()]
        if not task_list:
            print None
            return
        task_list.sort(key=lambda t: t.priority)
        maxTaskLength = max(len(t.name) for t in task_list)
        for t in task_list:
            if t.iscompleted:
                status = 'Complete'
            else:
                status = 'Open    '
            print str(t.priority)+'\t'+status+'\t'+(t.name + ' '*maxTaskLength)[:maxTaskLength]+'\t'+t.assigner
           # print '\t'+str(t.description)+'\n'

    def timedeltaToDaysString(self, td):
        if abs(td) < datetime.timedelta(1):
            output = str(abs(td).seconds / 3600)+':'+('00'+str(abs(td).seconds / 60))[-2:]
        else:
            output = str(abs(td).days)+' days'
#            output = str(abs(td).days)+' days, '+('00'+str(abs(td).seconds / 3600))[-2:]+':'+('00'+str(abs(td).seconds / 60))[-2:]
        if td < datetime.timedelta(0):
            # overdue timedelta
            return 'overdue by '+output
        else:
            return output

    def timedeltaToHoursString(self, td):
        s = td.seconds +  24 * 60 * 60 * td.days
        h = s / 60 / 60
        m = int(s / 60 % 60)
        return str(h)+':'+('00'+str(m))[-2:]

    def do_debug(self, arg):
        "enters debug mode"
        import pudb; pudb.set_trace()

    def do_updateTimeSpent(self, arg):
        if not self.selected_task: print 'select a task first'; return
        self.selected_task.timespent = hours.get_hours_worked_on_single_task(self.selected_task.id)
        print self.selected_task.timespent

    def do_meeting(self, arg):
        title = raw_input("Meeting Name: ")
        description = raw_input("Description: ")
        hours.clock_meeting_time(title=title, description=description)

    def do_clockHours(self, arg):
        if not self.selected_task: print 'select a task first'; return
        if arg and len(arg.split()) % 2 == 0:
            hours.clock_time(
                    self.selected_task.id,
                    title=self.selected_task.name,
                    description=self.selected_task.description,
                    start_datetime=parse.parseTimeInterval(' '.join(arg.split()[:len(arg.split()/2)])),
                    end_datetime=parse.parseTimeInterval(' '.join(arg.split()[arg.split()/2:]))
            )
        else:
            hours.clock_time(
                    self.selected_task.id,
                    title=self.selected_task.name,
                    description=self.selected_task.description)
        print 'hours clocked'

    def do_clear(self, arg):
        for i in range(100):
            print ''

if __name__ == '__main__':
    cli = EditTasksCLI()
    cli.cmdloop()
