from datetime import datetime

import indicators
from utils import tick_boundaries

class CandleWrapper(object):
    """wrap a candle so that the date can be accessed by candle.date and 
    open, high, low, close can be accessed by candle.open, candle.high, etc.
    """
    def __init__(self, candles, index):
        candles = candles[:] # make a copy otherwise it becomes recursive
        self.timestamp = candles[index][0]
        self.open  = candles[index][1]
        self.high  = candles[index][2]
        self.low   = candles[index][3]
        self.close = candles[index][4]
    
    def __getitem__(self, i):
        if   i == 0: return self.timestamp
        elif i == 1: return self.open
        elif i == 2: return self.high
        elif i == 3: return self.low
        elif i == 4: return self.close
        else:
            raise IndexError, "index out of range: %s" % i
        
    def __str__(self):
        date = datetime.fromtimestamp(self.timestamp)
        return "%s: %s, %s, %s, %s" % (date, self.open, self.high, self.low, self.close)

class TickCandles(list):
    """tick-based candles for a given period (in minutes)"""
    def __init__(self, period):
        self.period = period
        self.current = None # current virtual candle
                
    def process_tick(self, tick):
        timestamp, value = tick['timestamp'], tick['value'] 
        self.current = self.current or [tick_boundaries(timestamp, self.period), 
            value, value, value, value]
        if timestamp <= self.current[0]:
            self.current[4] = value # reset close
            if value > self.current[2]: # compare with high
                self.current[2] = value # update high
            elif value < self.current[3]: # compare with low
                self.current[3] = value # update low
        else:
            self.append(tuple(self.current))
            # TODO: think about this roll-over
            if (datetime.utcfromtimestamp(timestamp).date() > 
                datetime.utcfromtimestamp(self.current[0]).date()):
                # next UTC day, do not fill gap
                self.current = [tick_boundaries(timestamp, self.period), value, 
                    value, value, value]
            else:
                # same day, fill gaps if needed
                candle_time = self.current[0] + (self.period * 60)
                while timestamp > candle_time: # fill gaps
                    close = self.current[4]
                    self.append((candle_time, close, close, close, close))
                    candle_time += self.period * 60
                self.current = [candle_time, value, value, value, value]
    
    def __getattr__(self, name):
        # gets the indicators and calculates them
        # example on: 
        # http://mail.python.org/pipermail/python-list/2002-April/141153.html
        func = getattr(indicators, name)
        if func:
            c = self.__class__
            c.temp_method = func
            meth = self.temp_method
            del c.temp_method
            self.__setattr__(name, meth)
            return getattr(self, name)
        
    def __getitem__(self, i):
        return CandleWrapper(self, i) 
        
class TickWrapper(object):
    """wrap a tick so that the date can be accessed by tick.date and
    the value can be accessed by tick.value
    """
    def __init__(self, ticks, index):
        ticks = ticks[:] # make a copy otherwise it becomes recursive
        self.timestamp = ticks[index]['timestamp']
        self.value = ticks[index]['value']
    
    def __getitem__(self, i):
        if   i == 0: return self.timestamp
        elif i == 1: return self.value
        else:
            raise IndexError, "index out of range: %s" % i
        
    def __str__(self):
        date = datetime.fromtimestamp(self.timestamp)
        return "%s -> %s" % (date, self.value)
    
class Ticks(list):
    """define a tick list"""
    def __init__(self):
        self.cache = {}
        
    def candles(self, period):
        candles_key = period
        cs, start_index = self.cache.get(candles_key, (TickCandles(period), 0))
        for tick in self[start_index:]:
            cs.process_tick(tick)
        self.cache[candles_key] = cs, len(self)
        return cs
    
    def cs(self, period):
        """alias for candles(self, ...)"""
        return self.candles(period)
    
    def __getitem__(self, i):
        return TickWrapper(self, i) 
    
class Ticker(object):
    """hold ticker data"""
    def __init__(self, *args, **kwargs):
        self.ticks = Ticks()
        self.__dict__.update(kwargs)
            
    def __str__(self):
        return "symbol: %(symbol)s, type: %(secType)s, expiry: %(expiry)s" % self.__dict__

    def create_contract(self):
        contract = {}
        contract['symbol'] = self.symbol
        contract['secType'] = self.secType
        contract['expiry'] = getattr(self, 'expiry', None)
        contract['exchange'] = self.exchange
        contract['currency'] = self.currency
        return contract
    