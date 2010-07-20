#!/usr/bin/python
# make templated docs
# thomasballinger@gmail.com

import os, sys, optparse
import datetime
import calendarHours as hours
import spreadsheetTask as task
from pprint import pprint
from jinja2 import Environment, PackageLoader
import webbrowser
import tempfile

scriptDir = os.path.basename(os.path.abspath(__file__))


env = Environment(loader=PackageLoader(scriptDir, 'templates'))

def showTasks():
    template = env.get_template('weekTemplate.html')
    task_list = task.createTasks()
    (f, fname) = tempfile.mkstemp()
    f.write(template.render(task_list = task_list))
    webbrowser.open(fname)

if __name__ == '__main__':
    showTasks()
