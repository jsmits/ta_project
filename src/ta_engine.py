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
        order_entry = self.orders.get(message['order_id'], None)
        if not order_entry: return # not for this instance
        order_entry.update(message)
        # if this is a Filled entry order -> create and send STOP/LIMIT order
        strategy = order_entry.get('strategy')
        if strategy and order_entry['order']['type'] == "LMT_entry" \
            and message['status'] == 'Filled' and \
            not order_entry.get("exit_handled", False):
            ticker_id = order_entry['tick'].id
            ticker = self.tickers.get(ticker_id)
            order_entry['exit_handled'] = True # to avoid doubles, sometimes 
            # a entry fill is confirmed 2 times
            self.exit_order_request(ticker, strategy)
    
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
        ticker_id = tick['id']
        ticker = self.tickers.get(ticker_id)
        strategy = ticker.strategy
        if not strategy: return
        position = self.has_position(ticker)
        #if strategy.inside_trading_time(tick):
        if not position:
            order_id = self.pending_order_id(ticker_id, "LMT_entry")
            if not order_id:
                for s in strategy:
                    st = s.check_entry(ticker)
                    if st: 
                        self.limit_order_request(ticker, st)
                        break
        """
        else:
            if position < 0: 
                order_id = self.pending_order_id(ticker_id, "STPLMT")
                if order_id: self.cancel_order(order_id)
                self.market_order_request(ticker, "BUY")
            elif position > 0: 
                order_id = self.pending_order_id(ticker_id, "STPLMT")
                if order_id: self.cancel_order(order_id)
                self.market_order_request(ticker, "SELL")
            else:
                order_id = self.pending_order_id(ticker_id, "LMT")
                if order_id: self.cancel_order(order_id)
        """
        
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
        
    def pending_order_id(self, ticker_id, type):
        order_ids = self.order_map.get(ticker_id)
        if order_ids:
            last_order_id = order_ids[-1]
            order_entry = self.orders[last_order_id]
            if "Submit" in order_entry['status'] and \
                order_entry['order']['type'] == type:
                return last_order_id
    
    # order utility methods
    def get_next_valid_id(self):
        order_id = self.next_id
        if not order_id: 
            raise NoValidOrderIdException()
        self.next_id += 1 # this is done for speed
        self.publish_next_id(self.next_id)
        return order_id
        
    def publish_next_id(self, order_id):
        obj = {'type': "next_valid_id", 'value': order_id}
        self.handle_outgoing(obj, '/topic/account')
    
    def new_order_entry(self, ticker, order, **kw):
        tick = ticker.ticks[-1] # last tick == trigger tick
        ticker_id = tick.id
        order_entry = {'tick': tick, 'order': order, 
            'order_timestamp': time.time(), 'status': 'PendingSubmit'}
        order_entry.update(kw)
        order_id = order['order_id']
        self.orders[order_id] = order_entry
        order_ids = self.order_map.get(ticker_id, [])
        order_ids.append(order_id)
        self.order_map[ticker_id] = order_ids
        return order_id
    
    def create_order(self, ticker, action, type, **kw):
        order = {}
        order_id = self.get_next_valid_id()
        order['order_id'] = order_id
        order['action'] = action
        order['quantity'] = ticker.quantity
        order['type'] = type
        order.update(kw)
        return order
    
    def get_signal(self, strategy):
        signal = strategy.signal.__name__
        if   signal.startswith('entry_long'):  return "BUY"
        elif signal.startswith('entry_short'): return "SELL"
        else: 
            log.error('unknown signal: "%s"' % signal)
            
    # request methods
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
        
    def market_order_request(self, ticker, action):
        contract = ticker.create_contract()
        order = self.create_order(ticker, action, "MKT")
        self.new_order_entry(ticker, order)
        request = {'type': 'place_order', 'order': order, 'contract': contract}
        self.handle_outgoing(request)
        
    def limit_order_request(self, ticker, strategy):
        tick = ticker.ticks[-1] # trigger tick
        contract = ticker.create_contract()
        action = self.get_signal(strategy) # determine by strategy signal
        order = self.create_order(ticker, action, "LMT_entry", 
            trigger_timestamp=tick.timestamp, limit=tick.value)
        self.new_order_entry(ticker, order, strategy=strategy)
        request = {'type': 'place_order', 'order': order, 'contract': contract}
        self.handle_outgoing(request)
    
    def exit_order_request(self, ticker, strategy):
        contract = ticker.create_contract()
        action, stop, limit = strategy.exit_params() # determine by strategy signal
        ocagroup = repr(time.time())
        stop_order = self.create_order(ticker, action, "STP", 
            stop=stop, ocagroup=ocagroup)
        self.new_order_entry(ticker, stop_order, strategy=strategy)
        request = {'type': 'place_order', 'order': stop_order, 
            'contract': contract}
        self.handle_outgoing(request)
        limit_order = self.create_order(ticker, action, "LMT_exit", 
            limit=limit, ocagroup=ocagroup)
        self.new_order_entry(ticker, limit_order, strategy=strategy)
        request = {'type': 'place_order', 'order': limit_order, 
            'contract': contract}
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
        
        
        
