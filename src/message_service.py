import sys
import logging

import stomp

log = logging.getLogger("messaging")

class MessagingGateway(stomp.ConnectionListener):
    
    def __init__(self, messaging_connection):
        self.mconn = messaging_connection
        self.mconn.add_listener(self)
        
    def __log(self, frame_type, headers, body):
        log.debug("received frame: type=%s, headers=%r, body=%r" % (frame_type, headers, body))
        
    def start(self):
        self.mconn.start()
        
    # stomp connection listener methods
    def on_connecting(self, host_and_port):
        log.info("connecting messaging gateway...")
        self.mconn.connect()
        
    def on_connected(self, headers, body):
        self.__log("CONNECTED", headers, body)
        log.info("messaging gateway connected")

    def on_disconnected(self):
        log.info("messaging gateway disconnected")
        
    def on_message(self, headers, body):
        self.__log("MESSAGE", headers, body)
        
    def on_receipt(self, headers, body):
        self.__log("RECEIPT", headers, body)
        
    def on_error(self, headers, body):
        self.__log("ERROR", headers, body)
        
    # send methods
    def ack(self, message_id, transid=None):
        if transid:
            self.mconn.ack(message_id=message_id, transaction=transid)
        else:
            self.mconn.ack(message_id=message_id)
        
    def abort(self, transid):
        self.mconn.abort(transaction=transid)
        
    def begin(self, args):
        trans_id = self.mconn.begin()
        log.debug('transaction id: %s' % trans_id)
        
    def commit(self, transid):
        log.debug('committing %s' % transid)
        self.mconn.commit(transaction=transid)
   
    def disconnect(self):
        try:
            self.mconn.disconnect()
            log.info("disconnecting messaging gateway...")
        except stomp.NotConnectedException:
            pass # ignore if no longer connected
        
    def send(self, destination, message):
        self.mconn.send(destination=destination, message=message)
        log.debug('send to destination "%s" message: "%s"' % (destination, message))
        
    def sendtrans(self, destination, message, transid):
        self.mconn.send(destination=destination, message=message, 
                             transaction=transid)
        
    def subscribe(self, destination, ack='auto'):
        log.info('subscribing to "%s" with acknowledge: "%s"' % (destination, ack))
        self.mconn.subscribe(destination=destination, ack=ack)
        
    def unsubscribe(self, destination):
        log.info('unsubscribing from "%s"' % destination)
        self.mconn.unsubscribe(destination=destination)
