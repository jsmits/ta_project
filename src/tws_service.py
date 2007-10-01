from datetime import datetime, timedelta
import time
import stomp
import sys
from utils import message_encode, message_decode
from com.ib.client import EWrapper, EClientSocket, Contract, Order

class ResponseWrapper(EWrapper):
    """custom wrapper implementation"""
    def __init__(self): 
        self.handler = None
        
    def nextValidId(self, orderId):
        """this method is only called once upon connection"""
        message = {'type': "next_valid_id", 'value': orderId}
        self.handler.handle_outgoing(message)

    def tickPrice(self, tickerId, field, price, canAutoExecute):
        time = datetime.now()
        if field == 4: # last value
            message = {'type': "tick", 'id': tickerId, 'date': time,
                'value': price}
            self.handler.handle_tick(message)
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
        permId, parentId, lastFillPrice, clientId): 
        time = datetime.now()
        message = {'type': 'order_status', 'order_id': orderId, 'time': time, 
            'status': status, 'filled': filled, 'remaining': remaining,
            'fill_value': avgFillPrice, 'last_fill_price': lastFillPrice}
        self.handler.handle_outgoing(message)
    
    def updateAccountValue(self, key, value, currency, accountName):
        try: 
            value = float(value)
        except ValueError, info: 
            pass
        message = {'type': 'account_value', 'key': key, 'value': value,
                   'currency': currency}
        self.handler.handle_outgoing(message)
            
    def updatePortfolio(self, contract, position, marketPrice, marketValue, 
        averageCost, unrealizedPNL, realizedPNL, accountName): 
        message = {'type': 'portfolio_update', 'symbol': contract.m_symbol,
            'expiry': contract.m_expiry, 'position': position, 
            'market_price': marketPrice, 'market_value': marketValue,
            'average_cost': averageCost, 'unrealizedPNL': unrealizedPNL,
            'realizedPNL': realizedPNL}
        self.handler.handle_outgoing(message)
    
    def historicalData(self, reqId, date, open, high, low, close, volume, 
        count, WAP, hasGaps): 
        try:
            mtype = "tick"
            d = datetime(*time.localtime(int(date))[:-3])
            candle = d, open, high, low, close, volume
            if d.second == 0:
                message = {'type': mtype, 'id': reqId, 'date': 
                           d - timedelta(seconds=57), 'value': open}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'date': 
                           d - timedelta(seconds=44), 'value': high}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'date': 
                           d - timedelta(seconds=28), 'value': low}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'date': 
                           d - timedelta(seconds=7), 'value': close}
                self.handler.handle_tick(message)
            else:
                base_date = datetime(d.year, d.month, d.day, d.hour, d.minute)
                delta = timedelta(seconds=d.second/5.0)
                for i in range(1,5):
                    base_date += delta
                    message = {'type': mtype, 'id': reqId, 'date': base_date,
                               'value': candle[i]}
                    self.handler.handle_tick(message)
        except ValueError:
            # send last historical candle message
            message = {'type': "tick_hist_last", 'id': reqId}
            self.handler.handle_tick(message)
    
    def error(self, *args):
        if args and len(args) == 3: 
            args = list(args)
            args.insert(0, datetime.now())
            print "%s, error :: id: %s, code: %s, message: %s" % tuple(args)
        elif args and len(args) == 1:
            print "%s, exception :: %s" % (datetime.now(), args)
        elif args:
            print args
        else:
            print "%s, error method called without arguments" % str(datetime.now())

    def connectionClosed(self): 
        print "connection closed at %s" % str(datetime.now())
    
    # not implemented methods
    def openOrder(self, orderId, contract, order): pass    
    def tickSize(self, tickerId, field, size): pass
    def tickOptionComputation(self, tickerId, field, impliedVol, delta, 
        modelPrice, pvDividend): pass
    def updateAccountTime(self, timeStamp): pass
    def contractDetails(self, contractDetails): pass
    def bondContractDetails(self, contractDetails): pass
    def execDetails(self, orderId, contract, execution): pass
    def updateMktDepth(self, tickerId, position, operation, side, price, size): 
        pass
    def updateMktDepthL2(self, tickerId, position, marketMaker, operation, 
        side, price, vsize): pass
    def updateNewsBulletin(self,msgId, msgType, message, origExchange): pass
    def managedAccounts(self,accountsList): pass
    def receiveFA(self, faDataType, xml): pass
    def scannerParameters(self, xml): pass
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, 
        projection): pass
    def tickGeneric(self, tickerId, tickType, value): pass
    def tickString(self, tickerId, tickType, value): pass
        
class TWSEngine(stomp.ConnectionListener):
    """handle the trading related requests"""
    def __init__(self, host='127.0.0.1', port=7496, client_id=0):
        self.mgw = None
        self.host = host
        self.port = port
        self.client_id = client_id
        self.response_wrapper = ResponseWrapper()
        self.connection = EClientSocket(self.response_wrapper)
        self.response_wrapper.handler = self
        
    def start(self):
        # first start the messaging gateway
        self.mgw.start() # start the messaging gateway
        
    def exit(self):
        if self.connection.connected: self.disconnect()
        self.mgw.unsubscribe('/queue/request')
        self.mgw.disconnect()
    
    def connect(self):
        print "connecting to IB gateway..."
        self.connection.eConnect(self.host, self.port, self.client_id)
        
    def disconnect(self):
        print "disconnecting IB gateway..."
        self.connection.eDisconnect()
        
    # message handler methods
    def handle_outgoing(self, obj, queue='/topic/account'):
        message = message_encode(obj)
        self.mgw.send(queue, message)
        
    def handle_incoming(self, message):
        mtype = message['type']
        method = getattr(self, "process_%s" % mtype, None)
        if not method: 
            print "no processor found for message type: %s" % mtype
        else:
            method(message)
        
    def handle_tick(self, tick):
        queue = '/queue/ticks/%s' % tick['id']
        self.handle_outgoing(tick, queue)
        
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
        self.mgw.subscribe('/queue/request')
        # connect and request the account, order, and portfolio updates
        self.connect()
        tries = 10
        while not self.connection.connected:
            time.sleep(5)
            if not self.connection.connected:
                if tries == 0:
                    print "trading gateway connection failed"
                    return
                print "tws connection trying again..."
                self.connect()
                tries -= 1
            else:
                break
        self.connection.reqAccountUpdates(True, "")
        self.connection.reqOpenOrders()

    def on_message(self, headers, body):
        self.__print_message("MESSAGE", headers, body)
        try:
            message = message_decode(body)
            self.handle_incoming(message)
        except:
            print "unable to decode message body: %s" % body
            
    # incoming message processing      
    def process_place_order(self, message): 
        message_contract = message['contract']
        message_order = message['order']
        order_id = message_order['order_id']
        contract = self.create_contract(message_contract)
        order = self.create_order(message_order)
        self.place_order(order_id, contract, order)
        
    def process_cancel_order(self, message): 
        order_id = message['order_id']
        self.cancel_order(order_id)
        
    def process_historical_data_request(self, message):
        ticker_id = message['ticker_id']
        message_contract = message['contract']
        self.historical_data_request(ticker_id, message_contract)
        
    def process_tick_request(self, message):
        ticker_id = message['ticker_id']
        message_contract = message['contract']
        self.tick_request(ticker_id, message_contract)
        
    def process_cancel_market_data(self, message):
        ticker_id = message['ticker_id']
        self.cancel_market_data(ticker_id)
        
    def create_contract(self, c):
        contract = Contract()
        contract.m_symbol = c['symbol']
        contract.m_secType = c['secType']
        contract.m_expiry = c['expiry']
        contract.m_exchange = c['exchange']
        contract.m_currency = c['currency']
        return contract    
    
    def create_order(self, o):
        order = Order()
        order.m_orderId = o['order_id']
        order.m_clientId = self.client_id
        order.m_action = o['action']
        order.m_totalQuantity = o['quantity']
        order.m_orderType = 'MKT' # guaranteed execution
        order.m_lmtPrice = 0
        order.m_auxPrice = 0
        return order
        
    def place_order(self, order_id, contract, order):
        self.connection.placeOrder(order_id, contract, order)
        
    def cancel_order(self, order_id):
        self.connection.cancelOrder(order_id)
        
    def historical_data_request(self, ticker_id, ticker_contract, 
            duration="2 D", bar_size="1 min"):
        contract = self.create_contract(ticker_contract)
        now = datetime.now()
        enddate = now + timedelta(hours=1)
        enddatestr = enddate.strftime("%Y%m%d %H:%M:%S")
        self.connection.reqHistoricalData(ticker_id, contract, enddatestr, 
            duration, bar_size, "TRADES", 0, 2)
        
    def tick_request(self, ticker_id, ticker_contract):
        contract = self.create_contract(ticker_contract)
        self.connection.reqMktData(ticker_id, contract, None)
        
    def cancel_market_data(self, ticker_id):
        # cancel market Data
        self.connection.cancelMktData(ticker_id)

    def historical_data_handler(self, id, candles):
        print "Processing historical ticks for ticker %s." % id
        ticker = self.tickers.get(id)
        contract = self.__create_contract(ticker)
        self.connection.reqMktData(id, contract, None)
        for candle in candles:
            try:
                date_int = int(candle[0])
            except ValueError:
                continue
            else:
                localtime = time.localtime(date_int)
                date = datetime(*localtime[:-3])
                o, h, l, c = candle[1:5]
                if date.second == 0:
                    ticker.ticks.append((date - timedelta(seconds=57), o))
                    ticker.ticks.append((date - timedelta(seconds=44), h))
                    ticker.ticks.append((date - timedelta(seconds=28), l))
                    ticker.ticks.append((date - timedelta(seconds= 7), c))
                else:
                    base_date = datetime(date.year, date.month, date.day, 
                                         date.hour, date.minute)
                    delta = timedelta(seconds=date.second/5.0)
                    for i in range(1,5):
                        base_date += delta
                        ticker.ticks.append((base_date, candle[i]))
        self.requested_ticks.remove(id)

