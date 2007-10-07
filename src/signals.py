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

def tops_signal_generator(long_short_signal_pair):
    """generates long and short signals"""
    l_options = [60, 30, 20, 15, 10, 5, 4, 3]
    s_options = [20, 15, 10, 5, 4, 3, 2, 1]
    long_signals = []
    short_signals = []
    for generator in long_short_signal_pair:
        for lo in l_options:
            for so in s_options:
                if so * 2 < lo:
                    new = (generator, (lo, so))
                    if generator.__name__.startswith("entry_long"):
                        long_signals.append(new)
                    elif generator.__name__.startswith("entry_short"):
                        short_signals.append(new)
    for s in long_signals:
        print "generated (long): l=%s, s=%s" % s[1]
    for s in short_signals:
        print "generated (short): l=%s, s=%s" % s[1]
    long_output  = [s[0](*s[1]) for s in long_signals]
    short_output = [s[0](*s[1]) for s in short_signals]
    return long_output, short_output
          
if __name__ == '__main__':
    longs, shorts = tops_signal_generator(available_signals)
    
