from datetime import datetime
import time

def run_simulation(ticker, ticks, strategy):
    orders = {}
    order_id = 1
    open_order = False
    first_day_date = datetime.fromtimestamp(ticks[-1]['timestamp']).date()
    for tick in ticks:
        t.ticks.append(tick)
        tick_date = datetime.fromtimestamp(tick['timestamp']).date()
        if tick_date == first_day_date: continue # skip historic date
        tick_value = tick['value']
        if open_order:
            order = orders[order_id]
            signal = order['signal']
            name = str(signal)
            entry_value = order['entry_value']
            entry_time = order['order_timestamp']
            if name.startswith("entry_long"):
                if tick_value >= order['limit'] or \
                   tick_value <= order['stop']:
                    order.update({'exit_value': tick_value, 
                        'delta': tick_value - entry_value, 
                        'exit_time': tick['timestamp'],
                        'timespan': tick['timestamp']-entry_time})
                    order_id += 1
                    open_order = False
            elif name.startswith("entry_short"):
                if tick_value <= order['limit'] or \
                   tick_value >= order['stop']:
                    order.update({'exit_value': tick_value, 
                        'delta': entry_value - tick_value, 
                        'exit_time': tick['timestamp'],
                        'timespan': tick['timestamp']-entry_time})
                    order_id += 1
                    open_order = False
        else:
            for signal in strategy:
                processed_signal = signal.check_entry(ticker)
                ps = processed_signal
                if ps:
                    orders[order_id] = {'signal': ps, 
                        'order_value': tick_value,
                        'order_timestamp': tick['timestamp'], 'entry_value':
                        ps.target, 'stop': ps.stop, 'limit': ps.limit} 
                    open_order = True
                    break
    return orders
    
if __name__ == '__main__':
    
    from signals import strategy_builder, tops_signal_params_generator
    from signals import random_strategies_generator, create_strategy_map
    from tickdata import ES_ticks, SP_ticks
    from ticker import Ticker
    
    tops_signal_args = tops_signal_params_generator()
    nr_of_strategies = 50
    random_strategy_args = random_strategies_generator(tops_signal_args, 
                                                       output=nr_of_strategies)
    strategy_map = create_strategy_map(random_strategy_args)
    
    # setup
    start = datetime(2003, 7, 24)
    end = datetime(2003, 7, 26)
    #ticks = ES_ticks(start, end)
    
    SP_date = datetime(2005, 10, 27)
    print "loading and parsing tick data..."
    ticks = SP_ticks(SP_date)
    print "tick data loaded..."
    
    tt0 = time.time()
    for id, map in strategy_map.items():
        t = Ticker(increment=0.10)
        strategy = strategy_builder(map['params'])
        t0 = time.time()
        orders = run_simulation(t, ticks, strategy)
        t1 = time.time()
        map['orders'] = orders
        map['simulation_time'] = t1 - t0
        print "tested strategy: %s" % id
    tt1 = time.time()
    print "running %s simulations took %s seconds" % (nr_of_strategies, 
                                                      repr(tt1 - tt0))
    
    reduced_map = {}
    for id, map in strategy_map.items():
        orders = map['orders']
        deltas = [details['delta'] for details in orders.values() 
                  if details.get('delta')]
        negatives = [delta for delta in deltas if delta <= 0]
        positives = [delta for delta in deltas if delta > 0]
        pos_perc = None
        if positives:
            pos_perc = len(positives) * 100.0 / len(deltas)
        average_delta = None
        sum_delta = None
        if deltas:
            average_delta = sum(deltas) / len(deltas)
            sum_delta = sum(deltas)
        map['summary'] = {'average_delta': average_delta, 'positives':
                          pos_perc, 'orders': len(orders), 
                          'sum_delta': sum_delta}
        if average_delta and average_delta > 0 and pos_perc >= 50:
            reduced_map[id] = map
        
            

