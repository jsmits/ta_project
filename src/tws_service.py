from datetime import datetime, timedelta
import time
import logging

import stomp
from utils import message_encode, message_decode
from com.ib.client import EWrapper, EClientSocket, Contract, Order

log = logging.getLogger("server")

class ResponseWrapper(EWrapper):
    """custom wrapper implementation"""
    def __init__(self): 
        self.handler = None
        
    def nextValidId(self, orderId):
        """this method is only called once upon connection"""
        message = {'type': "next_valid_id", 'value': orderId}
        self.handler.handle_outgoing(message)

    def tickPrice(self, tickerId, field, price, canAutoExecute):
        if field == 4: # last value
            message = {'type': "tick", 'id': tickerId, 'timestamp': time.time(),
                'value': price}
            self.handler.handle_tick(message)
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
        permId, parentId, lastFillPrice, clientId): 
        message = {'type': 'order_status', 'order_id': orderId, 
            'status': status, 'filled': filled, 'remaining': remaining,
            'fill_value': avgFillPrice, 'last_fill_price': lastFillPrice,
            'timestamp': time.time()}
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
            timestamp = int(date)
            seconds = timestamp % 60
            candle = timestamp, open, high, low, close, volume
            if seconds == 0:
                message = {'type': mtype, 'id': reqId, 'value': open, 
                    'timestamp': timestamp - 57}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'value': high, 
                    'timestamp': timestamp - 44}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'value': low, 
                    'timestamp': timestamp - 28}
                self.handler.handle_tick(message)
                message = {'type': mtype, 'id': reqId, 'value': close, 
                    'timestamp': timestamp - 7}
                self.handler.handle_tick(message)
            else:
                timestamp_seconds = timestamp % 60
                base_timestamp = timestamp - timestamp_seconds
                delta_seconds = seconds / 5.0
                for i in range(1, 5):
                    base_timestamp += delta_seconds
                    message = {'type': mtype, 'id': reqId,
                        'value': candle[i], 'timestamp': base_timestamp}
                    self.handler.handle_tick(message)
        except ValueError:
            message = {'type': "tick_hist_last", 'id': reqId}
            self.handler.handle_tick(message)
    
    def error(self, *args):
        if len(args) == 3: 
            id, code, message = args
            self.handler.handle_message_code(id, code, message)
        elif args:
            log.error(args)
        else:
            log.warning("error method called without arguments")

    def connectionClosed(self): 
        # TODO: handle this? trying to reconnect
        log.info("TWS connection closed")
    
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
        self.requested_market_data = {} # memory in case of connection loss
        
    def start(self):
        self.mgw.start() # start the messaging gateway
        
    def exit(self):
        if self.connection.connected: self.disconnect()
        self.mgw.unsubscribe('/queue/request')
        self.mgw.disconnect()
    
    def connect(self):
        log.info("connecting to TWS...")
        self.connection.eConnect(self.host, self.port, self.client_id)
        
    def disconnect(self):
        log.info("disconnecting IB gateway...")
        self.connection.eDisconnect()
        
    # stomp connection listener methods
    def on_connected(self, headers, body):
        self.mgw.subscribe('/queue/request')
        # connect and request the account, order, and portfolio updates
        self.connect()
        tries = 10
        while not self.connection.connected:
            time.sleep(5)
            if not self.connection.connected:
                if tries == 0:
                    log.error("trading gateway connection failed")
                    return
                log.error("tws connection trying again...")
                self.connect()
                tries -= 1
            else:
                break
        log.info("connection to TWS established")
        self.account_data_request()
        
    def on_message(self, headers, body):
        try:
            message = message_decode(body)
        except:
            log.error("unable to decode message body: %s" % body)
        else:
            self.handle_incoming(message)
        
    # message handler methods
    def handle_outgoing(self, obj, topic_or_queue='/topic/account'):
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
        
    def handle_tick(self, tick):
        queue = '/queue/ticks/%s' % tick['id']
        self.handle_outgoing(tick, queue)
        
    def handle_message_code(self, id, code, m):
        critical = [1100, 1300]
        error = [1101, 2100, 2101, 2103]
        warning = [2102, 2105]
        if id != -1:
            message = "id: %s, code: %s, message: %s" % (id, code, m)
        else:
            message = "code: %s, message: %s" % (code, m)
        if code in critical: log.critical(message)
        elif code <= 1000 or code in error:
            if code in [165]: log.info(message)
            else: log.error(message)
        elif code in warning: log.warning(message)
        else: log.info(message)
        # code 1101: Connectivity between IB and TWS has been restored- data lost.*
        # *Market and account data subscription requests must be resubmitted
        # code 2100: New account data requested from TWS.  
        # API client has been unsubscribed from account data. **
        # **Account data subscription requests must be resubmitted
        if code in [1101, 2100]:
            self.account_data_request()
            if code == 1101:
                # TODO: PM: let client handle this (also with historical gap fill)
                # e.g. send a message with type 'error' to the /topic/account with the code 1101
                for id, contract in self.requested_market_data.items():
                    self.tick_request(id, contract)
            
    # incoming message processors   
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
        
    # order methods
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
    
    # TWS request methods
    def account_data_request(self):
        self.connection.reqAccountUpdates(True, "")
        self.connection.reqOpenOrders()
    
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
        self.requested_market_data[ticker_id] = ticker_contract
        
    def cancel_market_data(self, ticker_id):
        if self.requested_market_data.get(ticker_id, None):
            self.connection.cancelMktData(ticker_id)
            del self.requested_market_data[ticker_id]


