"""Module for getting authentication data for local applications"""
import getpass
import os
import copy
from stat import *

def _check_file_permissions(authfilename):
    """Returns True if the file permissions look ok on the file"""
    st = os.stat(authfilename)
    if not (st.st_mode & S_IRUSR and st.st_mode & S_IWUSR):
        # if user doesn't have read and write permissions
        print "You don't have permission to edit the ~/.auth file"
        return False
    if (st.st_mode & S_IRGRP or st.st_mode & S_IWGRP or st.st_mode & S_IXGRP):
        # if group has any permissions:
        print 'WARNING!  group has some permissions on this file.  Delete it right now!'
        return False
    if (st.st_mode & S_IROTH or st.st_mode & S_IWOTH or st.st_mode & S_IXOTH):
        # if group has any permissions:
        print 'WARNING!  others have some permissions on this file.  Delete it right now!'
        return False
    return True

def get_authentication(*keys):
    """Returns the values in the order requested, or False if there's some problem.

    If the string 'password' or 'pw' or a few other strings are in the key,
    then the getpass interface will be used to get the value from
    the user if it isn't already stored.

    Only characters that can be stored in a text file will work -
    if you password is more exotic than that, you're out of luck.
    Userkeys and password keys are stored in the same dictionary -
    hence, they need to have different names."""

    is_password = {}
    for key in keys:
        is_password[key] = False
        for s in ['password', 'pw', 'pass', 'secret', 'code', 'key', 'pword']:
            if s in key.lower():
                is_password[key] = True
                break

    if not os.name in ['posix']:
        print "I don't know the proper way to store this kind of data"
        print "on a non-posix operating system."
        print "I won't be able to save your credentials."
        credentials = []
        for key in userkeys:
            credentials.append(raw_input(key+':'))
        for key in pwkeys:
            credentials.append(getpass.getpass(key+':'))
        return credentials
    authfilename = os.path.expanduser('~/.auth')
    if os.path.exists(authfilename) and os.access(authfilename, os.R_OK):
        filecheck = _check_file_permissions(authfilename)
        if not filecheck:
            return False
        authfile = open(os.path.expanduser('~/.auth'))
        s = authfile.read()
        authfile.close()
        auth_dict = dict([(line[:line.index(':')], line[line.index(':')+1:]) for line in s.split('\n')])
    else:
        auth_dict = dict()

    orig_auth_dict = copy.deepcopy(auth_dict)
    credentials = []
    for key in keys:
        if key in auth_dict:
            credentials.append(auth_dict[key])
        else:
            if is_password[key]:
                value = getpass.getpass(key+":")
            else:
                value = raw_input(key+":")
            auth_dict[key] = value
            credentials.append(value)
    if auth_dict != orig_auth_dict:
        print "I'm going to ask you if you want to store these credentials"
        print "for next time.  Credentials are stored in your home folder"
        print "in plain text, with only file permissions protecting them."
        print "This means that anyone with root access could change the"
        print "permissions and view (or edit) them.  Think about it."
        store = raw_input('store credentials for next time? [y/N]')
        if store in ['Y', 'y', 'yes']:
            print 'saving credentials in '+authfilename
            authfile = open(authfilename,'w')
            authfile.write("\n".join([key+':'+value for key,value in zip(auth_dict.keys(), auth_dict.values())]))
            authfile.close()
            os.chmod(authfilename, S_IRUSR | S_IWUSR)
            if not _check_file_permissions(authfilename):
                return False
    return credentials

if __name__ == '__main__':
    print get_authentication('custom', 'mypw')
