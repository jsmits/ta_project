import pickle as pickle # pickle does a faster encoding than cPickle for jython !!!
import base64
from datetime import datetime
import time

try:
    import simplejson
except ImportError:
    simplejson = None
    
try:
    import cjson
except ImportError:
    cjson = None

def pickle_encode(obj):
    dp = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    de = base64.encodestring(dp)
    return de

def pickle_decode(obj):
    dd = base64.decodestring(obj)
    du = pickle.loads(dd)
    return du

def string_encode(obj):
    return repr(obj)

def string_decode(obj):
    return eval(obj)
 
def message_encode(obj):
    return string_encode(obj)

def message_decode(obj):
    return string_decode(obj)

def tick_boundaries(timestamp, period):
    # timestamp in seconds from 1970-01-01 00:00:00 (UTC)
    date = datetime.fromtimestamp(timestamp)
    minute = date.minute
    sm = minute - minute % period
    start_date = datetime(date.year, date.month, date.day, date.hour, sm, 0)
    start_timestamp = time.mktime(start_date.timetuple())
    end_timestamp = start_timestamp + (period * 60)
    return end_timestamp
    
if __name__ == '__main__':
    obj = {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25,
           'a' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'b' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'c' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'd' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'e' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'f' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'g' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'h' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'i' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'j' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'k' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'l' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'm' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'n' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'o' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'p' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'q' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'r' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           's' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           't' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'u' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'v' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25},
           'w' : {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25}
           }
    
    obj = {'id': 1, 'timestamp': 11425252551.982872, 'value': 1455.25}
    
    start = time.time()
    obj_enc = pickle_encode(obj)
    print "pickle encoding took: %s ms" % repr((time.time() - start) * 1000)
    start = time.time()
    obj_dec = pickle_decode(obj_enc)
    print "pickle decoding took: %s ms" % repr((time.time() - start) * 1000)
    
    try:
        start = time.time()
        obj_enc = simplejson.dumps(obj)
        print "simplejson encoding took: %s ms" % repr((time.time() - start) * 1000)
        start = time.time()
        obj_dec = simplejson.loads(obj_enc)
        print "simplejson decoding took: %s ms" % repr((time.time() - start) * 1000)
    except:
        pass
    
    try:
        start = time.time()
        obj_enc = cjson.encode(obj)
        print "cjson encoding took: %s ms" % repr((time.time() - start) * 1000)
        start = time.time()
        obj_dec = cjson.decode(obj_enc)
        print "cjson decoding took: %s ms" % repr((time.time() - start) * 1000)
    except:
        pass
    
    start = time.time()
    obj_enc = string_encode(obj)
    print "string encoding took: %s ms" % repr((time.time() - start) * 1000)
    start = time.time()
    obj_dec = string_decode(obj_enc)
    print "string decoding took: %s ms" % repr((time.time() - start) * 1000)
    
    number = 1000000
    times = []
    bst = time.time()
    for i in range(number):
        start = time.time()
        res = string_encode(obj)
        end = time.time() - start
        times.append(end * 1000)
    est = time.time()
    print "running string_encode %s times took %s ms" % (number, repr((est-bst) * 1000))
    print "min: %s ms, max: %s ms, avg: %s ms" % (min(times), max(times), sum(times)/len(times))
        
    
    