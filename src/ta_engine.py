import stomp
from utils import message_encode, message_decode

class TAEngine(stomp.ConnectionListener):
    """handle the trading related requests"""
    def __init__(self):
        self.mgw = None
        
    def start(self):
        # initialize the tickers, account, portfolio, etc.
        self.mgw.start() # start the messaging gateway
        return True
        
    def exit(self):
        self.mgw.disconnect()
    
    def handle_incoming(self, message):
        print "handling message: %s" % message
        
    # message handler methods
    def handle_outgoing(self, obj):
        message = message_encode(obj)
        self.mgw.send('/queue/request', message)
        
    def handle_error(self, *args):
        pass
    
    def __print_message(self, frame_type, headers, body):
        print "\r"
        print frame_type
        for header_key in headers.keys():
            print '%s: %s' % (header_key, headers[header_key])
        print
        print body
        
    # stomp connection listener methods
    def on_connected(self, headers, body):
        self.__print_message("CONNECTED", headers, body)
        self.mgw.subscribe('/queue/ticks') # use the ticker specific tick queue
        # like /queue/ticks/1
        self.mgw.subscribe('/topic/account')
        # request (historical) tick data

    def on_message(self, headers, body):
        self.__print_message("MESSAGE", headers, body)
        try:
            message = message_decode(body)
            self.handle_incoming(message)
        except:
            print "unable to decode message body: %s" % body
        
