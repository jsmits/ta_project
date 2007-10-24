import random

class Signal(object):
    def __init__(self, signal, args):
        self.signal = signal
        self.args = args # the args for building the signal
        self.target = None
        self.stop = None
        self.limit = None
        
    def check_entry(self, ticker):
        resp = self.signal(ticker)
        # response can be None, False, or a tuple with target, stop and limit
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
        return repr(self.args)

# mother of all long tops signals
def long_tops_signal_generator(period, low_top, high_top, stop_param, 
                               limit_param):
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
                               value > tops[-1].candle.high: # exclusion
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

def long_tops_2_signal_generator(period):
    def entry_long_tops_2_signal(ticker):
        """low top - HH - HL pattern
        one candle after the HL top candle (between HH high and HL low)
        one tick after this last candle (between HH high and HL low)"""
        ticks = ticker.ticks
        candles = ticks.candles(period)
        tops = candles.tops()
        if len(tops) >= 2: # pre-condition
            if tops[-3].is_low and tops[-2].is_HH and tops[-1].is_HL and \
               tops[-1].no_tops == 1: # condition 1
                if candles[-1].low > tops[-1].candle.low and \
                   candles[-1].high < tops[-2].candle.high:
                    ticks = candles.current_ticks
                    if len(ticks) == 1:
                        tick_value = ticks[-1][1] 
                        if tick_value > tops[-1].candle.low and \
                           tick_value < tops[-2].candle.high: # condition 3
                            target = tick_value
                            stop = tops[-1].candle.low
                            limit = tops[-2].candle.high
                            if (limit - target) < (target - stop):
                                limit = target + (target - stop)
                            return target, stop, limit
        return False
    return entry_long_tops_2_signal

# mother of all short tops signals
def short_tops_signal_generator(period, high_top, low_top, stop_param, 
                                limit_param):
    def entry_short_tops_signal(ticker):
        """high top - low top - 'virtual' LH - tick under low top's low"""
        ticks = ticker.ticks
        candles = ticks.candles(period)
        tops = candles.tops()
        if len(tops) >= 2: # pre-condition
            if getattr(tops[-2], "is_%s" % high_top) and \
               getattr(tops[-1], "is_%s" % low_top): # condition 1
                # check if the previous candle is a potential LH
                prev_candle = candles[-1]
                if prev_candle.high < tops[-2].candle.high and \
                   prev_candle.low > tops[-1].candle.low: # condition 2
                    current_ticks = candles.current_ticks
                    if current_ticks:
                        for timestamp, value in current_ticks[:-1]:
                            if value >= prev_candle.high or \
                               value < tops[-1].candle.low: # exclusion
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

def short_tops_2_signal_generator(period):
    def entry_short_tops_2_signal(ticker):
        """high top - LL - LH pattern
        one candle after the LH top candle (between LL low and LH high)
        one tick after this last candle (between LL low and LH high)"""
        ticks = ticker.ticks
        candles = ticks.candles(period)
        tops = candles.tops()
        if len(tops) >= 2: # pre-condition
            if tops[-3].is_high and tops[-2].is_LL and tops[-1].is_LH and \
               tops[-1].no_tops == 1: # condition 1
                if candles[-1].high < tops[-1].candle.high and \
                   candles[-1].low > tops[-2].candle.low:
                    ticks = candles.current_ticks
                    if len(ticks) == 1:
                        tick_value = ticks[-1][1] 
                        if tick_value < tops[-1].candle.high and \
                           tick_value > tops[-2].candle.low: # condition 3
                            target = tick_value
                            stop = tops[-1].candle.high
                            limit = tops[-2].candle.low
                            if (target - limit) < (stop - target):
                                limit = target - (stop - target)
                            return target, stop, limit
        return False
    return entry_short_tops_2_signal

# random signals for testing the API
def entry_long_random(ticker):
    if random.random() > 0.95:
        target = ticker.ticks[-1].value
        stop = target - 1.00
        limit = target + 1.00
        return target, stop, limit
    
def entry_short_random(ticker):
    if random.random() > 0.95:
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
    
    #for period in periods:
    #    for low_top, high_top in tops:
    #        for stop_param, limit_param in params:
    #            args.append(("long_tops", period, low_top, high_top, stop_param, 
    #                         limit_param))
    #            args.append(("short_tops", period, high_top, low_top, 
    #                         stop_param, limit_param))
                
    for period in periods:
        for stop_param, limit_param in params:
            args.append(("long_tops", period, 'low', 'HH', stop_param, 
                         limit_param))
            args.append(("short_tops", period, 'high', 'LL', stop_param, 
                         limit_param))
    return args

def random_strategies_generator(args=None, min=6, max=12, number=10000, 
                                exclude=[]):
    strategies = []
    tries = 0
    args = args or tops_signal_params_generator()
    while len(strategies) != number:
        nr_of_signals = random.choice(range(min, max))
        strategy = []
        for i in range(nr_of_signals):
            while True:
                s = random.choice(args)
                if s[:4] not in [strat[:4] for strat in strategy]:
                    strategy.append(s)
                    break
        if strategy not in strategies and strategy not in exclude:
            strategies.append(strategy)
        tries += 1
        if tries > 1000000:
            print "too many tries (%s): returning %s strategies" % (tries, 
                                                        len(strategies))
            break
    return strategies

def params_generator_2(min=3, max=8, number=20):
    params = []
    while len(params) != number:
        p1 = random.randint(min, max)
        p2 = random.randint(min, max)
        if (p1, p2) not in params:
            params.append((p1, p2))
    return params

def random_strategies_generator_2(periods=(1,2,5,10,15), strats_per_period=20):
    strategies = []
    for period in periods:
        params = params_generator_2(number=strats_per_period)
        for p1, p2 in params:
            strategies.append(
                (
                     ("long_tops", period, 'low', 'HH', p1, p2),
                     ("short_tops", period, 'high', 'LL', p1, p2)
                )
            )
    return strategies

def random_weeks_generator(days, number):
    weeks = []
    while len(weeks) != number:
        week = random.sample(days, 5)
        week.sort()
        if week not in weeks:
            weeks.append(week)
    return weeks

def create_strategy_map(strategy_args):
    map = {}
    id = 1
    for args in strategy_args:
        map[id] = {}
        map[id]['params'] = args
        id += 1
    return map

def strategy_builder(args):
    strategy = []
    for arg in args:
        generator = globals().get("%s_signal_generator" % arg[0])
        signal = generator(*arg[1:])
        strategy.append(Signal(signal, arg))
    return strategy
          
if __name__ == '__main__':
    
    tops_signal_args = tops_signal_params_generator()
    random_strategy_args = random_strategies_generator(tops_signal_args)
    strategy_map = create_strategy_map(random_strategy_args)
