from datetime import datetime
import time

from tickdata import ES_ticks
from ticker import Ticker
from signals import strategy_builder

t = Ticker(increment=0.25)
ticks = ES_ticks(datetime(2003, 8, 8))

signals_params = [('short_tops', 3, 'HH', 'low', 5, 6), 
          ('long_tops', 2, 'LL', 'high', None, None), 
          ('short_tops', 2, 'HH', 'low', 5, 8), 
          ('long_tops', 4, 'LL', 'HH', None, None), 
          ('short_tops', 10, 'high', 'low', 2, 3), 
          ('long_tops', 2, 'HL', 'high', 4, 2), 
          ('short_tops', 5, 'high', 'HL', 7, 4), 
          ('long_tops', 10, 'HL', 'HH', 3, 8), 
          ('long_tops', 10, 'low', 'high', 6, 3), 
          ('long_tops', 4, 'low', 'high', 6, 8)]

strategy = strategy_builder(signals_params)

def run_prof():
    t1 = time.time()
    for tick in ticks:
        t.ticks.append(tick)
        for signal in strategy:
            processed_signal = signal.check_entry(t)
    t2 = time.time()
    print "run_prof() took %s seconds to complete" % str(t2 - t1)
    return t

if __name__ == '__main__':
    t = run_prof()

