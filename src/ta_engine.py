from datetime import datetime

import stomp
from utils import message_encode, message_decode

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
        # initialize the tickers, account, portfolio, etc.
        self.mgw.start() # start the messaging gateway
        
    def exit(self):
        self.mgw.unsubscribe('/topic/account')
        for ticker_id in self.tickers.keys():
            self.cancel_market_data(ticker_id)
            self.mgw.unsubscribe('/queue/ticks/%s' % ticker_id)
        self.mgw.disconnect()
    
    # message handler methods
    def handle_outgoing(self, obj, topic_or_queue='/queue/request'):
        message = message_encode(obj)
        print "handle_outgoing, obj: %s, tq: %s" % (obj, topic_or_queue)
        self.mgw.send(topic_or_queue, message)
        
    def handle_error(self, *args):
        pass
    
    def handle_incoming(self, message):
        mtype = message['type']
        method = getattr(self, "process_%s" % mtype, None)
        if not method: 
            print "no processor found for message type: %s" % mtype
        else:
            method(message)
    
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
        self.mgw.subscribe('/topic/account')
        # request (historical) tick data
        for ticker_id, ticker in self.tickers.items():
            self.mgw.subscribe('/queue/ticks/%s' % ticker_id)
            self.historical_data_request(ticker_id, ticker)

    def on_message(self, headers, body):
        # TODO: log this messages
        # self.__print_message("MESSAGE", headers, body)
        try:
            message = message_decode(body)
        except:
            print "unable to decode message body: %s" % body
        else:
            self.handle_incoming(message)
    
    # incoming message processing      
    def process_tick(self, tick):
        print "tick: %s" % tick
        ticker_id = tick['id']
        ticker = self.tickers.get(ticker_id)
        ticker.ticks.append((tick['date'], tick['value']))
        if getattr(ticker, 'tradable', False): 
            self.analyze_tick(tick)
        
    def process_tick_hist_last(self, message):
        ticker_id = message['id']
        ticker = self.tickers.get(ticker_id)
        ticker.tradable = True
        self.tick_request(ticker_id, ticker)
    
    def process_next_valid_id(self, message):
        self.next_id = message.get('value')
        
    def get_next_valid_id(self):
        order_id = self.next_id
        self.increment_next_id(order_id)
        return order_id
        
    def increment_next_id(self, order_id):
        obj = {'type': "next_valid_id", 'value': order_id+1}
        self.handle_outgoing(obj, '/topic/account')
        
    def process_order_status(self, message):
        order = self.orders.get(message['order_id'], None)
        if not order: return # not for this instance
        order.update(message)
    
    def process_account_value(self, message):
        print "process_account_value, message: %s" % message
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
        if not strategy.inside_trading_time(tick['date']):
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
                    signal = strategy.check_exit(ticker, last_order['time'], 
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
            print "error :: unknown signal: %s" % signal
            return
        order_request = self.create_order_request(trigger_tick, signal, action)
        self.handle_outgoing(order_request)
        
    def create_order_request(self, trigger_tick, signal, action):
        ticker_id = trigger_tick['id']
        ticker = self.tickers.get(ticker_id)
        trigger_time = trigger_tick['date']
        trigger_value = trigger_tick['value']
        contract = self.create_contract(ticker)
        order_id = self.get_next_valid_id()
        order = self.create_order(order_id, ticker, action)
        order_entry = {'trigger_time': trigger_time, 'trigger_value': 
            trigger_value, 'signal': signal, 'order': order, 'status': 
            'PendingSubmit', 'order_time': datetime.now()}
        self.orders[order_id] = order_entry
        order_ids = self.order_map.get(ticker_id, [])
        order_ids.append(order_id)
        self.order_map[ticker_id] = order_ids
        return {'type': 'place_order', 'order': order, 'contract': contract}
    
    def create_contract(self, ticker):
        contract = {}
        contract['symbol'] = ticker.symbol
        contract['secType'] = ticker.secType
        contract['expiry'] = getattr(ticker, 'expiry', None)
        contract['exchange'] = ticker.exchange
        contract['currency'] = ticker.currency
        return contract
    
    def create_order(self, order_id, ticker, action):
        order = {}
        order['order_id'] = order_id
        order['action'] = action
        order['quantity'] = getattr(ticker, 'quantity', 1)
        return order
    
    def cancel_order(self, order_id):
        order_entry = self.orders[order_id]
        order_entry['status'] = 'PendingCancel'
        order_entry['time'] = datetime.now()
        request = {'type': 'cancel_order', 'order_id': order_id}
        self.handle_outgoing(request)
        
    def historical_data_request(self, ticker_id, ticker):
        contract = self.create_contract(ticker)
        request = {'type': 'historical_data_request', 'ticker_id': ticker_id,
            'contract': contract}
        self.handle_outgoing(request)
        
    def tick_request(self, ticker_id, ticker):
        contract = self.create_contract(ticker)
        request = {'type': 'tick_request', 'ticker_id': ticker_id,
            'contract': contract}
        self.handle_outgoing(request)
        
    def cancel_market_data(self, ticker_id):
        request = {'type': 'cancel_market_data', 'ticker_id': ticker_id}
        self.handle_outgoing(request)
        
        
        
