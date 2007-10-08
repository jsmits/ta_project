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
        
class SignalWrapper(object):
    def __init__(self, signal):
        self.signal = signal
        self.target = None
        self.stop = None
        self.limit = None
        
    def check_entry(self, ticker):
        resp = self.signal(ticker)
        # response can be None, False, or a target with stop and limit tuple
        if resp:
            # get the response params
            self.target, self.stop, self.limit = resp 
            return self
        
    def exit_params(self):
        signal_name = self.signal.__name__
        if signal_name.startswith('entry_long'): action = "SELL"
        elif signal_name.startswith('entry_short'): action = "BUY"
        return action, self.stop, self.limit
    
    def __str__(self):
        return self.signal.__name__
    
    def __repr__(self):
        return "SignalWrapper(%s)" % self.signal.__name__

# mother of all long tops signals
def long_tops_signal_generator(period, low_top, high_top, stop_param, limit_param):
    def entry_long_tops_signal(ticker):
        """low top - high top - 'virtual' HL - tick above high top's high"""
        ticks = ticker.ticks
        candles = ticks.candles(period)
        tops = candles.tops()
        if len(tops) >= 2: # pre-condition
            if getattr(tops[-2], "is_%s" % low_top) and \
               getattr(tops[-1], "is_%s" % high_top): # condition 1
                # check if the previous candle is a virtual HL
                prev_candle = candles[-1]
                if prev_candle.low > tops[-2].candle.low and \
                   prev_candle.high < tops[-1].candle.high: # condition 2
                    current_ticks = candles.current_ticks
                    if current_ticks:
                        for timestamp, value in current_ticks[:-1]:
                            if value <= prev_candle.low or \
                               value > tops[-1].candle.high: # exclusion condition
                                return False
                        current_tick = current_ticks[-1][1] 
                        if current_tick > tops[-1].candle.high: # condition 3
                            target = current_tick
                            if stop_param and limit_param: # predefined bracket
                                stop = target - stop_param * ticker.increment
                                limit = target + limit_param * ticker.increment
                            else: # dynamic bracket
                                stop = prev_candle.low
                                limit = target + (target - prev_candle.low)
                            return target, stop, limit
        return False
    return entry_long_tops_signal

# mother of all short tops signals
def short_tops_signal_generator(period, high_top, low_top, stop_param, limit_param):
    def entry_short_tops_signal(ticker):
        """high top - low top - 'virtual' LH - tick under low top's low"""
        ticks = ticker.ticks
        candles = ticks.candles(period)
        tops = candles.tops()
        if len(tops) >= 2: # pre-condition
            if tops[-2].is_HH and tops[-1].is_HL: # condition 1
                # check if the previous candle is a potential LH
                prev_candle = candles[-1]
                if prev_candle.high < tops[-2].candle.high and \
                   prev_candle.low > tops[-1].candle.low: # condition 2
                    current_ticks = candles.current_ticks
                    if current_ticks:
                        for timestamp, value in current_ticks[:-1]:
                            if value >= prev_candle.high or \
                               value < tops[-1].candle.low: # exclusion condition
                                return False
                        current_tick = current_ticks[-1][1] 
                        if current_tick < tops[-1].candle.low:
                            target = current_tick
                            if stop_param and limit_param: # predefined bracket
                                stop = target + stop_param * ticker.increment
                                limit = target - limit_param * ticker.increment
                            else: # dynamic bracket
                                stop = prev_candle.high
                                limit = target - (prev_candle.high - target)
                            return target, stop, limit
        return False
    return entry_short_tops_signal

# random signals for testing the API
def entry_long_random(ticker):
    if r.random() > 0.95:
        target = ticker.ticks[-1].value
        stop = target - 1.00
        limit = target + 1.00
        return target, stop, limit
    
def entry_short_random(ticker):
    if r.random() > 0.95:
        target = ticker.ticks[-1].value
        stop = target + 1.00
        limit = target - 1.00
        return target, stop, limit
    
def tops_signal_params_generator(periods=[15, 10, 5, 4, 3, 2], 
        bracket_params=[None,None,None,None,None,None,None,None,2,3,4,5,6,7,8]):
    low_tops = ["LL", "HL", "low"]
    high_tops = ["LH", "HH", "high"]
    
    tops = []
    for h in high_tops:
        for l in low_tops:
            tops.append((l, h))
    
    params = []
    for stop_param in bracket_params:
        if not stop_param:
            params.append((None, None))
            continue
        for limit_param in bracket_params:
            if not limit_param:
                continue
            params.append((stop_param, limit_param))
            
    args = []
    for period in periods:
        for low_top, high_top in tops:
            for stop_param, limit_param in params:
                args.append(("long_tops", period, low_top, high_top, stop_param, 
                             limit_param))
                args.append(("short_tops", period, high_top, low_top, stop_param, 
                             limit_param))
    return args

def random_strategies_generator(args, output=10000):
    strategies = []
    tries = 0
    while len(strategies) != output:
        nr_of_signals = random.choice(range(1,11))
        strategy = []
        for i in range(nr_of_signals):
            while True:
                s = random.choice(args)
                if s not in strategy:
                    strategy.append(s)
                    break
        if strategy not in strategies:
            strategies.append(strategy)
        tries += 1
        if tries > 1000000:
            print "too many tries (%s): returning %s strategies" % (tries, 
                                                        len(strategies))
            break
    return strategies

def create_strategy_map(strategy_args):
    from strategies import SignalWrapper
    map = {}
    id = 1
    for args in strategy_args:
        map[id] = {}
        map[id]['args'] = args
        strategy = []
        for arg in args:
            generator = globals().get("%s_signal_generator" % arg[0])
            signal = generator(*arg[1:])
            strategy.append(SignalWrapper(signal))
        map[id]['strategy'] = strategy
        id += 1
    return map
          
if __name__ == '__main__':
    
    tops_signal_args = tops_signal_params_generator()
    random_strategy_args = random_strategies_generator(tops_signal_args)
    strategy_map = create_strategy_map(random_strategy_args)
