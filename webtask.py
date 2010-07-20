# yay script that gets hit for every page but static ones atm
from google.appengine.ext import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import time
import datetime
import parse
import spreadsheetByListTask as task
import calendarHours as hours


class Prefs(db.Model):
    whose = db.UserProperty()
    allowed = db.StringProperty(multiline=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('content goes here')
        self.response.out.write('Your name is '+user.nickname())

class TaskView(webapp.RequestHandler):
    def get(self, user, taskid):

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/(.+)/task/(.+)', TaskView)],
                                      ('/(.+)/prefs', EditPrefs)],
                                      ('/changeprefs', EditPrefs)],
                                     debug=True)

if __name__ == '__main__':
    run_wsgi_app(application)

