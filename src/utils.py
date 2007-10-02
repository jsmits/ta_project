import pickle as pickle # pickle does a faster encoding than cPickle for jython !!!
import base64
from datetime import datetime
import time
 
def message_encode(obj):
    dp = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    de = base64.encodestring(dp)
    return de

def message_decode(obj):
    dd = base64.decodestring(obj)
    du = pickle.loads(dd)
    return du

def tick_boundaries(timestamp, period):
    # timestamp in seconds from 1970-01-01 00:00:00 (UTC)
    date = datetime.fromtimestamp(timestamp)
    minute = date.minute
    sm = minute - minute % period
    start_date = datetime(date.year, date.month, date.day, date.hour, sm, 0)
    start_timestamp = time.mktime(start_date.timetuple())
    end_timestamp = start_timestamp + (period * 60)
    return start_timestamp, end_timestamp