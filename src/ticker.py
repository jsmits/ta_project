from datetime import datetime
from numpy import zeros

import indicators
from utils import tick_boundaries

class Candle(object):
    """wrap a single candle so that the date can be accessed by candle.date and 
    open, high, low, close can be accessed by candle.open, candle.high, etc.
    """
    def __init__(self, candle):
        self.timestamp = candle[0]
        self.open      = candle[1]
        self.high      = candle[2]
        self.low       = candle[3]
        self.close     = candle[4]
    
    def __getitem__(self, i):
        if   i == 0: return self.timestamp
        elif i == 1: return self.open
        elif i == 2: return self.high
        elif i == 3: return self.low
        elif i == 4: return self.close
        else:
            try:
                int(i)
            except ValueError:
                raise KeyError, i
            else:
                raise IndexError, "index out of range: %s" % i

    def __str__(self):
        date = datetime.fromtimestamp(self.timestamp)
        return "%s: %s, %s, %s, %s" % (date, self.open, self.high, self.low, self.close)

class ArrayTickCandles(object):
    
    def __init__(self, period, days=None):
        self.period = period
        self.current_ticks = []
        self.cache = {}
        day_span = days or 2
        rows = (day_span * 1440) / period
        self.array = zeros((rows, 5), float)
        self.current_index = None
        
    def __init_array(self, first_values):
        self.array[0] = first_values
        delta = self.period * 60
        tm = self.array[0][0] # first timestamp
        for row in self.array[1:]: # skip the first row
            tm += delta
            row[0] = tm
        self.current_index = 0
        
    def process_tick(self, tick):
        timestamp, value = tick.timestamp, tick.value
        a = self.array
        ci = self.current_index
        c_row = a[ci]
        if ci is None:
            first_values = [tick_boundaries(timestamp, self.period), 
                                            value, value, value, value]
            self.__init_array(first_values)
        if timestamp <= c_row[0]:
            self.current_ticks.append((timestamp, value))
            c_row[4] = value # close
            if value > c_row[2]: c_row[2] = value # update high
            elif value < c_row[3]: c_row[3] = value # update low
        else:
            last_close = c_row[4]
            self.current_index += 1
            self.current_ticks = []
            while timestamp > a[self.current_index][0]:
                a[self.current_index][1:] = [last_close] * 4
                self.current_index += 1
            a[self.current_index][1:] = [value] * 4
        
class TickCandles(list):
    """tick-based candles for a given period (in minutes)"""
    def __init__(self, period):
        self.period = period
        self.current = None # current virtual candle
        self.current_ticks = []
        self.cache = {}
                
    def process_tick(self, tick):
        timestamp, value = tick.timestamp, tick.value
        self.current = self.current or [tick_boundaries(timestamp, self.period), 
                                            value, value, value, value]
        if timestamp <= self.current[0]:
            self.current_ticks.append((timestamp, value))
            self.current[4] = value # reset close
            if value > self.current[2]: # compare with high
                self.current[2] = value # update high
            elif value < self.current[3]: # compare with low
                self.current[3] = value # update low
        else:
            self.append(tuple(self.current))
            self.current_ticks = [] # reset the current_ticks list
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
                
    def tops(self):
        # for tops an exception is made; this indicator is so important, that
        # it got a separate method calcaluting tops via a Tops instance and
        # caching the results as much as possible
        key = "tops"
        tops, start_index = self.cache.get(key, (indicators.Tops(), 0))
        for candle in self[start_index:]:
            tops.process_candle(candle)
        self.cache[key] = tops, len(self)
        return indicators.TopsWrapper(tops.candles, tops)
    
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
        
    def append(self, candle):
        candle = Candle(candle)
        list.append(self, candle)
        
class Tick(object):
    """wrap a tick so that the date can be accessed by tick.date and
    the value can be accessed by tick.value
    """
    def __init__(self, tick):
        self.id = tick.get('id') # optional
        self.timestamp = tick['timestamp']
        self.value = tick['value']
    
    def __getitem__(self, i):
        if   i == 0: return self.timestamp
        elif i == 1: return self.value
        else:
            try:
                int(i)
            except ValueError:
                raise KeyError, i
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
    
    def append(self, tick):
        tick = Tick(tick)
        list.append(self, tick)
    
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
    