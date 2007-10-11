from datetime import datetime
from tickdata import get_ticks
from signals import strategy_builder
from ticker import Ticker
import threading
import time

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
        for tick in self.ticks:
            self.ticker.ticks.append(tick)
            tick_date = datetime.fromtimestamp(tick['timestamp'])
            # skip non-trading hours
            if tick_date.hour <= self.start[0] and tick_date.minute < self.start[1]: 
                continue 
            if tick_date.hour >= self.end[0] and tick_date.minute > self.end[1]:
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

    def create_order(self, tick, signal):
        tick_value = tick['value']
        self.orders[self.order_id] = {'signal': signal, 'order_value': tick_value,
            'order_timestamp': tick['timestamp'], 'entry_value': signal.target, 
            'stop': signal.stop, 'limit': signal.limit} 
        self.open_order = True
        
    def check_exit(self, tick, open_order):
        order = open_order
        signal = order['signal']
        signal_name = str(signal)
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
        signal = order['signal']
        signal_name = str(signal)
        delta_unc = None
        if signal_name.startswith("entry_long"):
            delta_unc = tick['value'] - entry_value
        if signal_name.startswith("entry_short"):
            delta_unc = entry_value - tick['value']
        delta = delta_unc - self.ticker.commission
        order.update({'delta_unc': delta_unc, 'delta': delta})
        self.order_id += 1
        self.open_order = False
        
class SimulationBot(threading.Thread):
    
    def __init__(self, queue, result):
        threading.Thread.__init__(self)
        self.queue = queue
        self.result = result
        
    def create_ticker(self, ticker_details):
        ticker = Ticker(**ticker_details)
        return ticker
    
    def create_ticks(self, ticker_details, day):
        symbol = ticker_details['symbol']
        ticks = get_ticks(symbol, day)
        return ticks
    
    def create_strategy(self, args):
        strategy = strategy_builder(args)
        return strategy
        
    def create_worker(self, task):
        ticker = self.create_ticker(task['ticker'])
        ticks = self.create_ticks(task['ticker'], task['day'])
        strategy = self.create_strategy(task['strategy_args'])
        worker = SimulationRunner(ticker, ticks, strategy)
        return worker
    
    def run(self):
        while True:
            task = self.queue.get()
            if task is None:
                break
            worker = self.create_worker(task)
            task_id = task['task_id']
            print "processing task %s by %s..." % (task_id, self.getName())
            t1 = time.time()
            result = worker.run()
            t2 = time.time()
            print "task %s completed in %s seconds" % (task_id, str(t2 - t1))
            self.result.append({task['task_id']: result})
            self.queue.task_done()