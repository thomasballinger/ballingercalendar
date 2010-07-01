import os, sys
import datetime
import string
import spreadsheetTask as task

def parseTimedelta(datestring):
    words = datestring.split()
    if len(words) == 1:
        try:
            int(words[0])
            return datetime.timedelta
        except ValueError:
            pass
    if datestring[-5:] == 'hours':
        try:
            return datetime.timedelta(0,int(datestring[:-5])*60*60) 
        except ValueError:
            pass
    if datestring[-4:] == 'days':
        try:
            return datetime.timedelta(int(datestring[:-4])) 
        except ValueError:
            pass
    if datestring[-3:] == 'day':
        try:
            return datetime.timedelta(1) 
        except ValueError:
            pass
    if datestring[-3:] == 'hour':
        try:
            return datetime.timedelta(0,1) 
        except ValueError:
            pass
    if datestring[-1:] == 'h':
        try:
            return datetime.timedelta(0,int(datestring[:-1])*60*60) 
        except ValueError:
            pass
    if datestring[-1:] == 'd':
        try:
            return datetime.timedelta(int(datestring[:-1])) 
        except ValueError:
            pass
    # parsing for days and hours together needs to be added

def parseDate(datestring):
    if datestring == 'tomorrow':
        return datetime.datetime.now()+datetime.timedelta(1)
    if datestring == 'next week':
        return datetime.datetime.now()+datetime.timedelta(7)
    nums = None
    if datestring.find('/')!=-1:
        parts = datestring.split('/')
        try:
            nums = [int(x) for x in parts]
        except ValueError:
            pass
    if datestring.find('-')!=-1:
        parts = datestring.split('-')
        try:
            nums = [int(x) for x in parts]
        except ValueError:
            pass
    if nums:
        try:       # month, day, year, hours, minutes
            return datetime.datetime(nums[2],nums[0],nums[1],nums[3],nums[4])
        except IndexError:
            try:   # month, day, year, hours
                return datetime.datetime(nums[2],nums[0],nums[1],nums[3])
            except IndexError:
                try:#month, day, year
                    return datetime.datetime(nums[2],nums[0],nums[1])
                except IndexError:
                    try:
                        return datetime.datetime(datetime.datetime.now().year,nums[0],nums[1])
                    except:
                        pass
    timedelta = parseTimedelta(datestring)
    if timedelta:
        output = datetime.datetime.now() + timedelta
    if output:
        return output
    raise Exception('could not parse date string')

def parseTimeInterval(datestring):
    '''last hour, today 4-6, today 4am to 8'''
    words = datestring.split()
    if len(words) == 1:
       return [datetime.datetime.now() - datetime.timedelta(0,60*60),
               datetune.datetime.now()]

def parseBoolean(b):
    if b == 'yes' or b == 'Yes' or b == 'y' or b == 'Y':
        return True
    else:
        return False
