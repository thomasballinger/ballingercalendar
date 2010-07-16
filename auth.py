
import getpass
import os

def getAuthentication():
    '''Returns username, password'''
    if os.path.exists(os.path.expanduser('~/.task')):
        f = open(os.path.expanduser('~/.task'))
        s = f.read()
        (username, password) = s.split()
    else:
        username = raw_input('gmail address:')
        password = getpass.getpass('password:')
        store = raw_input('store credentials for next time? [y/N]')
        if store in ['Y','y','yes']:
            f = open(os.path.expanduser('~/.task'),'w')
            f.write(username+'\n'+password)
            f.close()
            os.chmod(os.path.expanduser('~/.task'),0700)
    return (username, password)
