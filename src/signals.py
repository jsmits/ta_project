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
        return True
    
def entry_short_random(ticker):
    if r.random() > 0.95:
        return True

# possible params for tops signal generators
low_tops = ["LL", "HL", "low"]
high_tops = ["LH", "HH", "high"]
periods = [15, 10, 5, 4, 3, 2]
bracket_params = [0, 2, 3, 4, 5, 6, 7, 8]
          
if __name__ == '__main__':
    long_signal_generators, short_signal_generators = signal_generator(entry_long_tops_1, entry_short_tops_1)
    
