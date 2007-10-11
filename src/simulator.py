if __name__ == '__main__':
    
    from datetime import datetime
    import time
    
    from signals import strategy_builder, tops_signal_params_generator
    from signals import random_strategies_generator, create_strategy_map
    from tickdata import ES_ticks
    from ticker import Ticker
    from utils import random_weekday
    
    from simulation import SimulationRunner
    
    tops_signal_args = tops_signal_params_generator()
    nr_of_strategies = 10
    random_strategy_args = random_strategies_generator(tops_signal_args, 
                                                       output=nr_of_strategies)
    strategy_map = create_strategy_map(random_strategy_args)
    
    # setup
    start = datetime(2004, 1, 1)
    end   = datetime(2007, 1, 1)
    
    ticks = None
    print "picking random weekday..."
    while not ticks:
        weekday = random_weekday(start, end)
        print "random weekday: %s" % str(weekday)
        ticks = ES_ticks(weekday)
        if not ticks: print "no ticks found for: %s, trying again..." % str(weekday)
    print "tick data loaded..."
    
    tt0 = time.time()
    for id, map in strategy_map.items():
        t = Ticker(increment=0.25, commission=0.1)
        strategy = strategy_builder(map['params'])
        t0 = time.time()
        simulation = SimulationRunner(t, ticks, strategy)
        orders = simulation.run()
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
        if sum_delta > 0: print map['summary']
        
            

