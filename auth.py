import os
def getAuthentication():
    '''Returns username, password'''
    if os.path.exists(os.path.expanduser('~/.task')):
        f = open(os.path.expanduser('~/.task'))
        s = f.read()
        (username, password) = s.split()
    else:
        username = raw_input('gmail address:')
        password = raw_input('password:')
        store = raw_input('store credentials for next time? [y/N]')
        if store in ['Y','y','yes']:
            f = open(os.path.expanduser('~/.task'),'w')
            f.write(username+'\n'+password)
            f.close()
    return (username, password)
