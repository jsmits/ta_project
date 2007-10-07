import random
r = random.Random()

def ma_co(candles, ma_type, params, direction):
    "MA cross-over signal"
    if len(candles) > params: # pre-condition
        ma = getattr(candles, ma_type)(params)
        if direction == 1: # up
            if candles[-2][4] < ma[-2]: # cascading conditions
                if candles[-1][4] > ma[-1]:
                    return True
            return False
        if direction == -1: # down
            if candles[-2][4] > ma[-2]: # cascading conditions
                if candles[-1][4] < ma[-1]:
                    return True
            return False
        
def entry_long_tops_1(l, s):
    def signal(ticker):
        ticks = ticker.ticks
        tl = ticks.cs(l).tops()
        if len(tl) >= 2: # pre-condition
            if tl[-2].is_low and tl[-1].is_high: # condition 1
                candles = ticks.cs(s)
                ts = ticks.cs(s).tops()
                if ts[-1].is_low and ts[-1].low > tl[-2].low: # condition 2 and 3
                    if candles[-2].timestamp == ts[-1].timestamp and ts[-1].no_tops == 1: # condition 4 and 5
                        print "long generic 2, date=%s, l=%s, s=%s" % (str(ticks[-1].timestamp), l, s)
                        return True
        return False
    return signal

def entry_short_tops_1(l, s):
    def signal(ticker):
        ticks = ticker.ticks
        tl = ticks.cs(l).tops()
        if len(tl) >= 2: # pre-condition
            if tl[-2].is_high and tl[-1].is_low: # condition 1
                candles = ticks.cs(s)
                ts = ticks.cs(s).tops()
                if ts[-1].is_high and ts[-1].high < tl[-2].high: # condition 2 and 3
                    if candles[-2].timestamp == ts[-1].timestamp and ts[-1].no_tops == 1: # condition 4 and 5
                        print "short generic 2, timestamp=%s, l=%s, s=%s" % (str(ticks[-1].timestamp), l, s)
                        return True
        return False
    return signal

# random signals for testing the API
def entry_long_random(ticker):
    if r.random() > 0.95:
        return True
    
def entry_short_random(ticker):
    if r.random() > 0.95:
        return True

available_signals = [entry_long_tops_1, entry_short_tops_1]

def l_s_options_generator(l_options=[60, 30, 20, 15, 10, 5],
                          s_options=[20, 15, 10, 5, 3, 2, 1]):
    args = []
    for lo in l_options:
        for so in s_options:
            if so * 2 < lo:
                args.append((lo, so))
    return args

def signal_generator(long_generator, short_generator, args=[]):
    """generates long and short signal genrator based on the given args"""
    generator_args = args or l_s_options_generator()
    long_signals = [(long_generator, args) for args in generator_args]
    short_signals = [(short_generator, args) for args in generator_args]
    return long_signals, short_signals
          
if __name__ == '__main__':
    long_signal_generators, short_signal_generators = signal_generator(entry_long_tops_1, entry_short_tops_1)
    
