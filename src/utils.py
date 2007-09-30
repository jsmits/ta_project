import pickle as pickle # pickle does a faster encoding than cPickle for jython !!!
import base64
 
def message_encode(obj):
    dp = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    de = base64.encodestring(dp)
    return de

def message_decode(obj):
    dd = base64.decodestring(obj)
    du = pickle.loads(dd)
    return du