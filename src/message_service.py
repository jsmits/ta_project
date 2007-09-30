import sys

import stomp

class MessagingGateway(stomp.ConnectionListener):
    
    def __init__(self, messaging_connection):
        self.mconn = messaging_connection
        self.mconn.add_listener(self)
        
    def __print_async(self, frame_type, headers, body):
        print "\r",
        print frame_type
        for header_key in headers.keys():
            print '%s: %s' % (header_key, headers[header_key])
        print
        print body
        print '> ',
        sys.stdout.flush()
        
    def start(self):
        self.mconn.start()
        
    # stomp connection listener methods
    def on_connecting(self, host_and_port):
        self.mconn.connect()

    def on_disconnected(self):
        print "messaging gateway disconnected"
        
    def on_receipt(self, headers, body):
        self.__print_async("RECEIPT", headers, body)
        
    def on_error(self, headers, body):
        self.__print_async("ERROR", headers, body)
        
    # send methods
    def ack(self, message_id, transid=None):
        if transid:
            self.mconn.ack(message_id=message_id, transaction=transid)
        else:
            self.mconn.ack(message_id=message_id)
        
    def abort(self, transid):
        self.mconn.abort(transaction=transid)
        
    def begin(self, args):
        print 'transaction id: %s' % self.mconn.begin()
        
    def commit(self, transid):
        print 'committing %s' % transid
        self.mconn.commit(transaction=transid)
   
    def disconnect(self):
        try:
            self.mconn.disconnect()
            print "disconnected messaging gateway..."
        except stomp.NotConnectedException:
            pass # ignore if no longer connected
        
    def send(self, destination, message):
        self.mconn.send(destination=destination, message=message)
        
    def sendtrans(self, destination, message, transid):
        self.mconn.send(destination=destination, message=message, 
                             transaction=transid)
        
    def subscribe(self, destination, ack='auto'):
        print 'subscribing to "%s" with acknowledge: "%s"' % (destination, ack)
        self.mconn.subscribe(destination=destination, ack=ack)
        
    def unsubscribe(self, destination):
        print 'unsubscribing from "%s"' % destination
        self.mconn.unsubscribe(destination=destination)
