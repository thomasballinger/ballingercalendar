"""Module for getting authentication data for local applications"""
import getpass
import os

def get_authentication():
    """Returns username and password of current user either by asking
    or by getting them from a config file"""
    if os.path.exists(os.path.expanduser('~/.task')):
        authfile = open(os.path.expanduser('~/.task'))
        file_string = authfile.read()
        (username, password) = file_string.split()
    else:
        username = raw_input('gmail address:')
        password = getpass.getpass('password:')
        store = raw_input('store credentials for next time? [y/N]')
        if store in ['Y', 'y', 'yes']:
            authfile = open(os.path.expanduser('~/.task'),'w')
            authfile.write(username+'\n'+password)
            authfile.close()
            os.chmod(os.path.expanduser('~/.task'), 0700)
    return (username, password)
