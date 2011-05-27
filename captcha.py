#!/usr/bin/python

# If Google is demanding a captcha, try this.
# Ryan Tucker, 2009/04/28

# Props to http://groups.google.com/group/google-apps-apis/browse_thread/thread/eea81678085b8904
# and franko353 <frank.wil...@gmail.com>

import gdata.apps.service
import getpass
import sys
import auth
import webbrowser

def getcaptcha(service):
        try:
                service.ProgrammaticLogin()
                #print "I just logged in successfully...?"
        except gdata.service.CaptchaRequired:
                captcha_token = service._GetCaptchaToken()
                url = service._GetCaptchaURL()
                print "Please go to this URL:"
                print "  " + url
                webbrowser.open(url)
                captcha_response = raw_input("Type the captcha image here: ")
                service.ProgrammaticLogin(captcha_token, captcha_response)
                print "Done!"
if __name__=='__main__':
    (username, password) = auth.get_authentication('gmailaddress', 'gmailpassword')
    service = gdata.apps.service.AppsService(email=username, password=password)
    getcaptcha(service)
