import psyco

def sma(self, params):
    input = []
    output = []
    for candle in self:
        value = candle[4]
        input.append(value)
        outputvalue = None
        if len(input) >= params:
            outputvalue = sum(input[(len(input)-params):len(input)]) / params
        output.append(outputvalue)
    return output

def ema(self, params):
    input = []
    output = []
    for candle in self:
        value = candle[4]
        input.append(value)
        outputvalue = None
        if len(input) == params: # first one is a sma
            outputvalue = sum(input[(len(input)-params):len(input)]) / params
        if len(input) > params:
            outputvalue = ((value-output[-1]) * (2.0/(1+params))) + output[-1]
        output.append(outputvalue)
    return output

class MacdWrapper(list):
    
    def __init__(self, params, short_ema, long_ema, macd):
        self.params = params
        self.short_ema = short_ema
        self.long_ema = long_ema
        self.extend(macd)
        
    def __ema(self):
        params = self.params
        input = []
        output = (params[1]-1) * [None]
        for value in self[params[1]-1:]:
            input.append(value)
            outputvalue = None
            if len(input) == params[2]: # first one is a sma
                outputvalue = (sum(input[(len(input)-params[2]):len(input)]) / 
                               params[2])
            if len(input) > params[2]:
                outputvalue = (((value - output[-1]) * (2.0 / (1+params[2]))) + 
                               output[-1])
            output.append(outputvalue)
        return output
    
    def __getattr__(self, name):
        if name == 'ema':
            return self.__ema()
        

def macd(self, params):
    short_ema = ema(self, params[0])
    long_ema = ema(self, params[1])
    output = []
    for i in range(len(self)):
        outputvalue = None
        if i+1 >= params[1]:
            outputvalue = short_ema[i] - long_ema[i]
        output.append(outputvalue)
    return MacdWrapper(params, short_ema, long_ema, output)

def atr(self, params):
    tr_output = []
    output = []
    for i in range(len(self)):
        candle = self[i]
        high = candle[2]
        low = candle[3]
        if i == 0:
            tr = high - low # (high - low) = initial tr
        else:
            pclose = self[i-1][4]
            tr = max(high - low, abs(high - pclose), abs(low - pclose))
        tr_output.append(tr)
        outputvalue = tr
        if len(tr_output) >= params:
            patr = output[-1]
            atr = ((patr * (params - 1)) + tr_output[-1]) / params
            outputvalue = atr
        output.append(outputvalue)
    return output

class TopCandleWrapper(object):
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.top = parent.tops[index]
        self.candle = parent.candles[index]
        
    def ux_is_high(self):
        return self.top in [2,12,22,32]
    
    def ux_is_HH(self):
        return self.top == 32
    
    def ux_is_LH(self):
        return self.top == 12
    
    def ux_is_low(self):
        return self.top in [1,11,21,31]
    
    def ux_is_HL(self):
        return self.top == 31
    
    def ux_is_LL(self):
        return self.top == 11
    
    def ux_timestamp(self):
        return self.candle[0]
    
    def ux_open(self):
        return self.candle[1]
    
    def ux_high(self):
        return self.candle[2]
    
    def ux_low(self):
        return self.candle[3]
    
    def ux_close(self):
        return self.candle[4]
    
    def ux_no_tops(self):
        """trailing non-tops after this top"""
        tops = self.parent.tops
        index =  self.index
        no_tops = 0
        while True:
            index += 1
            try:
                if tops[index] == 0: no_tops += 1
                else: break
            except IndexError:
                break
        return no_tops
    
    def __getattr__(self, name):
        """utility methods need a none __ prefix because with __ they are 
        considered private and then they are not accessible!
        """
        method = self.__getattribute__("ux_%s" % name)
        return method()
    
    def __str__(self):
        return "%s -> %s" % (self.top, self.candle)

class TopsWrapper(list):
    """Wrap the tops output and provide some utlity methods"""
    def __init__(self, candles, all_tops):
        self.candles = candles
        self.tops = all_tops
        self.top_indexes = []
        psyco.bind(getattr(self, 'top_index_generator'))
        
    def top_index_generator(self):
        indexes = []
        for i in range(len(self.tops)):
            if self.tops[i] != 0: 
                indexes.append(i)
        return indexes
    
    def __getitem__(self, i):
        if not self.top_indexes: 
            self.top_indexes = self.top_index_generator()
        index = self.top_indexes[i]
        return TopCandleWrapper(self, index) 
    
    def __getslice__(self, *args):
        if not self.top_indexes: 
            self.top_indexes = self.top_index_generator()
        indexes = list.__getslice__(self.top_indexes, *args)
        start, stop = indexes[0], indexes[-1] + 1 # 1 extra, to include last top
        candles = list.__getslice__(self.candles, start, stop)
        tops = list.__getslice__(self.tops, start, stop)
        return TopsWrapper(candles, tops)
        
    def __len__(self):
        if not self.top_indexes: 
            self.top_indexes = self.top_index_generator()
        return len(self.top_indexes)
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

class Tops(list):
    
    def __init__(self):
        self.mark = 0, 0 # temporary tops holder
        self.ph, self.pl = [], [] # previous high and low list
        self.candles = []
        
    def process_candle(self, candle):
        
        L = 1; LL = 11; EL = 21; HL = 31
        H = 2; LH = 12; EH = 22; HH = 32
        
        ph, pl = self.ph, self.pl
        high = candle[2]
        low  = candle[3]
        cs = self.candles
        cs.append(candle)
        
        if len(self) == 0: # first entry, can never be determined
            self.append(0)
        
        elif high <= cs[self.mark[0]][2] and low >= cs[self.mark[0]][3]: # inside bar
            self.append(0)
        
        elif high > cs[self.mark[0]][2] and low < cs[self.mark[0]][3]: # outside bar
            if ph == [] and pl == []:
                self.append(0)
                self.mark = len(self)-1, 0
            else:
                self.append(0) # added new code line 17-7-2006 !!!
                self[self.mark[0]] = 0
                for j in reversed(range(len(self)-1)):
                    if cs[j][2] > high or cs[j][3] < low: 
                        # first non-inclusive bar
                        break
                # checking for inbetween tops
                count = 0
                for k in range(j+1, len(self)-1): 
                    if self[k] != 0: # top found
                        count += 1
                        if self[k] in [L, LL, EL, HL]: 
                            pl.remove(k) # removing top indexes from list
                        if self[k] in [H, LH, EH, HH]: 
                            ph.remove(k) # idem
                        self[k] = 0 # reset top
                if count > 0:
                    if len(pl) and len(ph):
                        if (pl[-1] > ph[-1]): # if true, low is most recent
                            self.mark = len(self)-1, 2
                        elif (ph[-1] > pl[-1]): # high is most recent
                            self.mark = len(self)-1, 1
                    elif len(pl) and not len(ph):
                        self.mark = len(self)-1, 2
                    elif len(ph) and not len(pl):
                        self.mark = len(self)-1, 1
                    elif not len(pl) and not len(ph):
                        # current outside bar has become indifferent
                        self.mark = len(self)-1, 0 
                if count == 0:
                    # set same signal to current outside bar
                    self.mark = len(self)-1, self.mark[1] 
        
        elif high > cs[self.mark[0]][2] and low >= cs[self.mark[0]][3]: # upbar
            if self.mark[1]  < 2: # upbar with previous indifferent or low mark
                if pl == []: 
                    self[self.mark[0]] = L # L
                else:
                    if cs[self.mark[0]][3] < cs[pl[-1]][3]: 
                        self[self.mark[0]] = LL # LL
                    elif cs[self.mark[0]][3] == cs[pl[-1]][3]: 
                        self[self.mark[0]] = EL # EL
                    elif cs[self.mark[0]][3] > cs[pl[-1]][3]: 
                        self[self.mark[0]] = HL # HL
                pl.append(self.mark[0])
                self.mark = len(self), 2
                self.append(0)
            elif self.mark[1] == 2: # upbar with previous high self.mark
                self[self.mark[0]] = 0 # reset previous self.mark
                self.mark = len(self), 2
                self.append(0)
        
        elif high <= cs[self.mark[0]][2] and low < cs[self.mark[0]][3]: # downbar
            if self.mark[1] != 1: # downbar with previous indifferent or high mark
                if ph == []: 
                    self[self.mark[0]] = H # H
                else:
                    if cs[self.mark[0]][2] < cs[ph[-1]][2]: 
                        self[self.mark[0]] = LH # LH
                    elif cs[self.mark[0]][2] == cs[ph[-1]][2]: 
                        self[self.mark[0]] = EH # EH
                    elif cs[self.mark[0]][2]  > cs[ph[-1]][2]: 
                        self[self.mark[0]] = HH # HH
                ph.append(self.mark[0])
                self.mark = len(self), 1
                self.append(0)
            elif self.mark[1] == 1: # downbar with previous low mark
                self[self.mark[0]] = 0 # reset previous mark
                self.mark = len(self), 1
                self.append(0)

def tops(self):
    """Calculate tops
    0 - no top 
    1 - L; 11 - LL; 21 - EL; 31 - HL
    2 - H; 12 - LH; 22 - EH; 32 - HH
    """
    # signal constants   
    L  =  1
    LL = 11
    EL = 21
    HL = 31
    H  =  2
    LH = 12
    EH = 22
    HH = 32
    
    output = []
    mark = 0, 0
    ph, pl = [], [] # previous high and low list
    
    for i in range(len(self)):
        candle = self[i]
        high = candle[2]
        low = candle[3]
        
        if i == 0: # first entry, can never be determined
            output.append(0)
            continue
        
        if high <= self[mark[0]][2] and low >= self[mark[0]][3]: # inside bar
            output.append(0)
            continue
        
        if high > self[mark[0]][2] and low < self[mark[0]][3]: # outside bar
            if ph == [] and pl == []:
                output.append(0)
                mark = len(output)-1, 0
            else:
                output.append(0) # added new code line 17-7-2006 !!!
                output[mark[0]] = 0
                for j in reversed(range(len(output)-1)):
                    if self[j][2] > high or self[j][3] < low: 
                        # first non-inclusive bar
                        break
                # checking for inbetween tops
                count = 0
                for k in range(j+1, len(output)-1): 
                    if output[k] != 0: # top found
                        count += 1
                        if output[k] in [L, LL, EL, HL]: 
                            pl.remove(k) # removing top indexes from list
                        if output[k] in [H, LH, EH, HH]: 
                            ph.remove(k) # idem
                        output[k] = 0 # reset top
                if count > 0:
                    if len(pl) and len(ph):
                        if (pl[-1] > ph[-1]): # if true, low is most recent
                            mark = len(output)-1, 2
                        elif (ph[-1] > pl[-1]): # high is most recent
                            mark = len(output)-1, 1
                    elif len(pl) and not len(ph):
                        mark = len(output)-1, 2
                    elif len(ph) and not len(pl):
                        mark = len(output)-1, 1
                    elif not len(pl) and not len(ph):
                        # current outside bar has become indifferent
                        mark = len(output)-1, 0 
                if count == 0:
                    # set same signal to current outside bar
                    mark = len(output)-1, mark[1] 
            continue
        
        if high > self[mark[0]][2] and low >= self[mark[0]][3]: # upbar
            if mark[1]  < 2: # upbar with previous indifferent or low mark
                if pl == []: 
                    output[mark[0]] = L # L
                else:
                    if self[mark[0]][3] < self[pl[-1]][3]: 
                        output[mark[0]] = LL # LL
                    elif self[mark[0]][3] == self[pl[-1]][3]: 
                        output[mark[0]] = EL # EL
                    elif self[mark[0]][3] > self[pl[-1]][3]: 
                        output[mark[0]] = HL # HL
                pl.append(mark[0])
                mark = len(output), 2
                output.append(0)
            elif mark[1] == 2: # upbar with previous high mark
                output[mark[0]] = 0 # reset previous mark
                mark = len(output), 2
                output.append(0)
            continue 
        
        if high <= self[mark[0]][2] and low < self[mark[0]][3]: # downbar
            if mark[1] != 1: # downbar with previous indifferent or high mark
                if ph == []: 
                    output[mark[0]] = H # H
                else:
                    if self[mark[0]][2] < self[ph[-1]][2]: 
                        output[mark[0]] = LH # LH
                    elif self[mark[0]][2] == self[ph[-1]][2]: 
                        output[mark[0]] = EH # EH
                    elif self[mark[0]][2]  > self[ph[-1]][2]: 
                        output[mark[0]] = HH # HH
                ph.append(mark[0])
                mark = len(output), 1
                output.append(0)
            elif mark[1] == 1: # downbar with previous low mark
                output[mark[0]] = 0 # reset previous mark
                mark = len(output), 1
                output.append(0)
            continue
        
    return TopsWrapper(self, output)  

