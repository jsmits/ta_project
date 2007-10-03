from datetime import datetime
import logging
import time
import sys, traceback

import stomp
from utils import message_encode, message_decode

log = logging.getLogger("client")

class NoValidOrderIdException(Exception): pass

class TAEngine(stomp.ConnectionListener):
    """handle the trading related requests"""
    def __init__(self, tickers):
        self.mgw = None
        self.tickers = tickers
        self.account = {}
        self.portfolio = {}
        self.orders = {}
        self.order_map = {}
        self.next_id = None
        
    def start(self):
        self.mgw.start() # start the messaging gateway
        
    def exit(self):
        self.mgw.unsubscribe('/topic/account')
        for ticker_id in self.tickers.keys():
            self.cancel_market_data(ticker_id)
            self.mgw.unsubscribe('/queue/ticks/%s' % ticker_id)
        self.mgw.disconnect()
    
    # stomp connection listener methods
    def on_connected(self, headers, body):
        # initialize the tickers, account, portfolio, etc.
        self.mgw.subscribe('/topic/account')
        # request (historical) tick data
        for ticker_id, ticker in self.tickers.items():
            self.mgw.subscribe('/queue/ticks/%s' % ticker_id)
            log.info("requesting historical ticks for ticker id: %s" % ticker_id)
            self.historical_data_request(ticker_id, ticker)

    def on_message(self, headers, body):
        try:
            message = message_decode(body)
        except:
            log.error("unable to decode message body: %s" % body)
        else:
            self.handle_incoming(message)
            
    # message handler methods
    def handle_outgoing(self, obj, topic_or_queue='/queue/request'):
        message = message_encode(obj)
        log.debug("send: %r to '%s'" % (obj, topic_or_queue))
        self.mgw.send(topic_or_queue, message)
        
    def handle_incoming(self, message):
        log.debug("recv: %r" % message)
        mtype = message['type']
        method = getattr(self, "process_%s" % mtype, None)
        if not method: 
            log.error("no processor found for message type: %s" % mtype)
        else:
            method(message)
    
    # incoming message processors  
    def process_tick(self, tick):
        ticker_id = tick['id']
        ticker = self.tickers.get(ticker_id)
        ticker.ticks.append(tick)
        if getattr(ticker, 'tradable', False): 
            try:
                self.analyze_tick(tick)
            except Exception, e:
                log.error("exception in analyze tick, info: %s" % e)
                traceback.print_exc(file=sys.stdout)
        
    def process_tick_hist_last(self, message):
        ticker_id = message['id']
        ticker = self.tickers.get(ticker_id)
        ticker.tradable = True
        log.info("subscribing to tick stream for ticker id: %s" % ticker_id)
        self.tick_request(ticker_id, ticker)
    
    def process_next_valid_id(self, message):
        self.next_id = message.get('value')
        
    def process_order_status(self, message):
        order = self.orders.get(message['order_id'], None)
        if not order: return # not for this instance
        order.update(message)
    
    def process_account_value(self, message):
        key = message['key']
        value = message['value']
        currency = message['currency']
        if currency:
            d = self.account.get(key, {})
            d[currency] = value
            self.account[key] = d
        else:
            self.account[key] = value
    
    def process_portfolio_update(self, message):
        key = message['symbol']
        expiry = message['expiry']
        if expiry: key += "_%s" % expiry
        self.portfolio[key] = message
    
    # tick analyzing methods
    def analyze_tick(self, tick):
        id = tick['id']
        ticker = self.tickers.get(id)
        strategy = ticker.strategy
        if not strategy: return
        position = self.has_position(ticker)
        last_order = self.last_order(id)
        signal = None
        if not strategy.inside_trading_time(tick):
            # PM determine if pending request -> cancel
            if position < 0: signal = 'exit_short_TIME_EXIT'
            elif position > 0: signal = 'exit_long_TIME_EXIT'
        else:
            if not position:
                if not last_order or not 'Submit' in last_order['status']:
                    signal = strategy.check_entry(ticker)
            else:
                if last_order and last_order['status'] == 'Filled':
                    if position < 0: exit = 'short'
                    elif position > 0: exit = 'long'
                    signal = strategy.check_exit(ticker, last_order['timestamp'], 
                        last_order['fill_value'], exit)
                if not last_order:
                    if position < 0: signal = 'exit_short_SAFETY'
                    elif position > 0: signal = 'exit_long_SAFETY'
        self.handle_signal(tick, signal)

    def has_position(self, ticker):
        for key in self.portfolio.keys():
            if key == ticker.symbol or key.startswith("%s_" % ticker.symbol):
                position = self.portfolio[key]['position']
                return position

    def last_order(self, ticker_id):
        order_ids = self.order_map.get(ticker_id)
        if order_ids:
            last_order_id = order_ids[-1]
            order_entry = self.orders[last_order_id]
            return order_entry
    
    def handle_signal(self, trigger_tick, signal):
        if not signal: return
        # this is for futures
        if   signal.startswith('entry_long'):  action = 'BUY'
        elif signal.startswith('exit_long'):   action = 'SELL'
        elif signal.startswith('entry_short'): action = 'SELL'
        elif signal.startswith('exit_short'):  action = 'BUY'
        else:
            log.error('unknown signal: "%s"' % signal)
            return
        self.order_request(trigger_tick, signal, action)
    
    # order utility methods
    def get_next_valid_id(self):
        order_id = self.next_id
        if not order_id: 
            raise NoValidOrderIdException()
        self.publish_next_id(order_id+1)
        return order_id
        
    def publish_next_id(self, order_id):
        obj = {'type': "next_valid_id", 'value': order_id}
        self.handle_outgoing(obj, '/topic/account')
    
    def create_order_request(self, trigger_tick, signal, action):
        ticker_id = trigger_tick['id']
        ticker = self.tickers.get(ticker_id)
        trigger_timestamp = trigger_tick['timestamp']
        trigger_value = trigger_tick['value']
        contract = ticker.create_contract()
        order_id = self.get_next_valid_id()
        order = self.create_order(order_id, ticker, action)
        order_entry = {'trigger_value': trigger_value, 'signal': signal, 
            'order': order, 'order_timestamp': time.time(),
            'status': 'PendingSubmit', 'trigger_timestamp': trigger_timestamp}
        self.orders[order_id] = order_entry
        order_ids = self.order_map.get(ticker_id, [])
        order_ids.append(order_id)
        self.order_map[ticker_id] = order_ids
        log.debug("order entry (%s): %r (ticker: %s)" % (order_id, order_entry, ticker_id))
        return {'type': 'place_order', 'order': order, 'contract': contract}
    
    def create_order(self, order_id, ticker, action):
        order = {}
        order['order_id'] = order_id
        order['action'] = action
        order['quantity'] = ticker.quantity
        return order
    
    # request methods
    def order_request(self, trigger_tick, signal, action):
        try:
            order_request = self.create_order_request(trigger_tick, signal, action)
        except NoValidOrderIdException:
            log.error("no valid order id, stop server and client, start client, "\
                "and then start server")
            return
        self.handle_outgoing(order_request)
    
    def cancel_order(self, order_id):
        order_entry = self.orders[order_id]
        order_entry['status'] = 'PendingCancel'
        # TODO: PM: make this cancel_time and cancel_timestamp, if possible
        order_entry['timestamp'] = time.time()
        request = {'type': 'cancel_order', 'order_id': order_id}
        self.handle_outgoing(request)
        
    def historical_data_request(self, ticker_id, ticker):
        contract = ticker.create_contract()
        request = {'type': 'historical_data_request', 'ticker_id': ticker_id,
            'contract': contract}
        self.handle_outgoing(request)
        
    def tick_request(self, ticker_id, ticker):
        contract = ticker.create_contract()
        request = {'type': 'tick_request', 'ticker_id': ticker_id,
            'contract': contract}
        self.handle_outgoing(request)
        
    def cancel_market_data(self, ticker_id):
        request = {'type': 'cancel_market_data', 'ticker_id': ticker_id}
        self.handle_outgoing(request)
        
    # command-line commands
    def cl_help(self, args):
        """help command
        usage: help command
        """
        print "help command entered"
        
    def cl_last_tick(self, args):
        if len(args) == 1:
            print "please provide a ticker id"
            return
        ticker_id = int(args[1])
        ticker = self.tickers.get(ticker_id, None)
        if not ticker:
            print "unknown id"
            return
        if len(ticker.ticks) > 0:
            print "last tick for ticker '%s': %s" % (ticker_id, ticker.ticks[-1])
        else:
            print "no ticks available for ticker '%s'" % ticker_id
            
    def cl_tickers(self, args):
        items = self.tickers.items()
        if items:
            print "available tickers:"
            for id, ticker in items:
                print "%s -> %s" % (id, ticker)
        else:
            print "no tickers available"
            
    def cl_tops(self, args):
        ticker_id = int(args[1])
        period = int(args[2])
        ticker = self.tickers.get(ticker_id, None)
        if not ticker:
            print "unknown id"
            return
        number = 10
        tops = ticker.ticks.cs(period).tops()
        if len(args) == 4:
            number = int(args[3])
            lt = len(tops)
            if lt > number:
                tops = tops[-number:]
        for top in tops:
            print top
        
        
        
