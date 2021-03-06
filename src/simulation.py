from datetime import datetime
import time
from ticker import Ticker
from tickdata import get_ticks_2
from signals import strategy_builder

class SimulationRunner(object):
    
    def __init__(self, ticker, ticks, strategy, start=(8,30), end=(14,45)):
        self.ticker = ticker
        self.ticks = ticks
        self.strategy = strategy
        self.start = start
        self.end = end
        self.orders = {}
        self.order_id = 1
        self.open_order = False
        
    def run(self):
        # PM calculate start and end in epoch secs here
        for tick in self.ticks:
            self.ticker.ticks.append(tick)
            tick_date = datetime.fromtimestamp(tick['timestamp'])
            # skip non-trading hours
            tick_in_minutes = tick_date.hour * 60 + tick_date.minute
            if tick_in_minutes < self.start[0] * 60 + self.start[1]:
                continue 
            if tick_in_minutes >= self.end[0] * 60 + self.end[1]:
                if self.open_order:
                    order = self.orders[self.order_id]
                    self.close_order(tick, order)
                return self.orders # should be report?
            # check for exit
            if self.open_order:
                order = self.orders[self.order_id]
                self.check_exit(tick, order)
            # check for entry
            else:
                for signal in self.strategy:
                    processed_signal = signal.check_entry(self.ticker)
                    if processed_signal:
                        self.create_order(tick, processed_signal)
                        break
        return {}

    def create_order(self, tick, signal):
        tick_value = tick['value']
        self.orders[self.order_id] = {'signal': signal.args, 
            'signal_name': str(signal), 'order_value': tick_value,
            'order_timestamp': tick['timestamp'], 'entry_value': signal.target, 
            'stop': signal.stop, 'limit': signal.limit} 
        self.open_order = True
        
    def check_exit(self, tick, open_order):
        order = open_order
        signal_name = order['signal_name']
        tick_value = tick['value']
        if signal_name.startswith("entry_long") and \
            (tick_value >= order['limit'] or tick_value <= order['stop']):
            self.close_order(tick, order)
        if signal_name.startswith("entry_short") and \
            (tick_value <= order['limit'] or tick_value >= order['stop']):
            self.close_order(tick, order)
                
    def close_order(self, tick, open_order):
        order = open_order
        entry_value = order['entry_value']
        entry_time = order['order_timestamp']
        order.update({'exit_value': tick['value'], 'exit_time': tick['timestamp'],
            'timespan': tick['timestamp'] - entry_time})
        signal_name = order['signal_name']
        delta_unc = None
        if signal_name.startswith("entry_long"):
            delta_unc = tick['value'] - entry_value
        if signal_name.startswith("entry_short"):
            delta_unc = entry_value - tick['value']
        delta = delta_unc - self.ticker.commission
        order.update({'delta_unc': delta_unc, 'delta': delta})
        self.order_id += 1
        self.open_order = False
        
def create_ticker(ticker_details):
    ticker = Ticker(**ticker_details)
    return ticker

def create_ticks(ticker_details, day):
    symbol = ticker_details['symbol']
    ticks = get_ticks_2(symbol, day)
    return ticks

def create_strategy(args):
    strategy = strategy_builder(args)
    return strategy
    
def create_worker(task):
    ticker = create_ticker(task['ticker'])
    ticks = create_ticks(task['ticker'], task['day'])
    strategy = create_strategy(task['strategy_args'])
    worker = SimulationRunner(ticker, ticks, strategy)
    return worker
        
def process_func(queue, result):
    for task in iter(queue.get, 'STOP'):
        worker = create_worker(task)
        t1 = time.time()
        report = worker.run()
        t2 = time.time()
        td = t2 - t1
        if td < 1.5:
            print "ticks for day %s might be invalid -> low analysis "\
                "time: %s secs." % (task['day'], td)
        result.put({task['task_id']: report})
