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
        
    def __top_indexes(self):
        indexes = []
        for i in range(len(self.tops)):
            if self.tops[i] != 0: 
                indexes.append(i)
        return indexes
    
    def __getitem__(self, i):
        if not self.top_indexes: 
            self.top_indexes = self.__top_indexes()
        index = self.top_indexes[i]
        return TopCandleWrapper(self, index) 
    
    def __getslice__(self, *args):
        if not self.top_indexes: 
            self.top_indexes = self.__top_indexes()
        indexes = list.__getslice__(self.top_indexes, *args)
        start, stop = indexes[0], indexes[-1] + 1 # 1 extra, to include last top
        candles = list.__getslice__(self.candles, start, stop)
        tops = list.__getslice__(self.tops, start, stop)
        return TopsWrapper(candles, tops)
        
    def __len__(self):
        if not self.top_indexes: 
            self.top_indexes = self.__top_indexes()
        return len(self.top_indexes)
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

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
    
    inputhigh = []
    inputlow = []
    output = []
    
    mark = 0, 0
    ph = [] # previous high list
    pl = [] # previous low list
    
    for candle in self:
        high = candle[2]
        low = candle[3]
        inputhigh.append(high)
        inputlow.append(low)
        
        if len(inputhigh) == 1: # first entry, can never be determined
            output.append(0)
            continue
        
        if high <= inputhigh[mark[0]] and low >= inputlow[mark[0]]: # inside bar
            output.append(0)
            continue
        
        if high > inputhigh[mark[0]] and low < inputlow[mark[0]]: # outside bar
            if ph == [] and pl == []:
                output.append(0)
                mark = len(output)-1, 0
            else:
                output.append(0) # added new code line 17-7-2006 !!!
                output[mark[0]] = 0
                for j in reversed(range(len(output)-1)):
                    if inputhigh[j] > high or inputlow[j] < low: 
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
        
        if high > inputhigh[mark[0]] and low >= inputlow[mark[0]]: # upbar
            if mark[1]  < 2: # upbar with previous indifferent or low mark
                if pl == []: 
                    output[mark[0]] = L # L
                else:
                    if inputlow[mark[0]] < inputlow[pl[-1]]: 
                        output[mark[0]] = LL # LL
                    elif inputlow[mark[0]] == inputlow[pl[-1]]: 
                        output[mark[0]] = EL # EL
                    elif inputlow[mark[0]] > inputlow[pl[-1]]: 
                        output[mark[0]] = HL # HL
                pl.append(mark[0])
                mark = len(output), 2
                output.append(0)
            elif mark[1] == 2: # upbar with previous high mark
                output[mark[0]] = 0 # reset previous mark
                mark = len(output), 2
                output.append(0)
            continue 
        
        if high <= inputhigh[mark[0]] and low < inputlow[mark[0]]: # downbar
            if mark[1] != 1: # downbar with previous indifferent or high mark
                if ph == []: 
                    output[mark[0]] = H # H
                else:
                    if inputhigh[mark[0]] < inputhigh[ph[-1]]: 
                        output[mark[0]] = LH # LH
                    elif inputhigh[mark[0]] == inputhigh[ph[-1]]: 
                        output[mark[0]] = EH # EH
                    elif inputhigh[mark[0]]  > inputhigh[ph[-1]]: 
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

def ctops(self):
    """cacheable tops indicator
    Calculate tops
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
    
    for i in range(len(self)):
        candle = self[i]
        high = candle[2]
        low = candle[3]
        
        if i == 0: # first entry, can never be determined
            output.append(0)
            continue
        
        elif high <= self[i-1][2] and low >= self[i-1][3]: # inside bar
            output.append(0)
        
        elif high > self[i-1][2] and low < self[i-1][3]: # outside bar
            output.append(0)
            for j in range(i-1,-1,-1):
                if self[j][2] > high or self[j][3] < low: 
                    # first non-inclusive bar
                    break
                output[j] = 0 # reset all inbetween tops
        
        elif high > self[i-1][2] and low >= self[i-1][3]: # upbar
            if i == 1: # only one previous, so this must be an L
                output[0] = L
            elif self[i-1][2] <= self[i-2][2] and self[i-1][3] < self[i-2][3]:
                # previous low bar
                hm, lm = None, None
                for j in range(i-1,-1,-1): # look back for pre-previous low
                    # remember high low range, because if an outer is detected
                    # before the low looping should be stopped and the next 
                    # candle evaluated
                    outer_break = False
                    if not hm or not lm:
                        hm, lm = self[j][2], self[j][3]
                        continue
                    ## this is for outer detection, a difficult but important
                    # problem to tackle 
                    if self[j][2] >= hm and self[j][3] <= lm: # outer detected
                        # now it's important if the current candle is higher or
                        # lower than the outer, the outer should be evaluated for
                        # a top
                        if self[i][2] > self[j][2] or self[i][3] < self[j][3]:
                            for k in range(j-1,-1,-1):
                                outer_break_2 = False
                                if output[k] % 2 == 1: # low, no problem
                                    outer_break = True
                                    break # and break outer !!!!
                                elif output[k] != 0 and output[k] % 2 == 0: # high
                                    # now the outer is a low
                                    # check what kind of low
                                    # look back further for the next low
                                    for l in range(k-1,-1,-1): 
                                        if output[l] % 2 == 1: # low
                                            if   self[j][3]  < self[l][3]: output[j] = LL
                                            elif self[j][3]  > self[l][3]: output[j] = HL
                                            elif self[j][3] == self[l][3]: output[j] = EL 
                                            else: output[j] = L
                                            outer_break = True
                                            outer_break_2 = True
                                            break
                                if outer_break_2: break
                    if outer_break: break
                    ## end of outer detection block
                    if output[j] % 2 == 1: # low
                        if   self[i-1][3]  < self[j][3]: output[i-1] = LL
                        elif self[i-1][3]  > self[j][3]: output[i-1] = HL
                        elif self[i-1][3] == self[j][3]: output[i-1] = EL 
                        else: output[i-1] = L
                        break
                    if self[j][2] > hm: hm = self[j][2]
                    if self[j][3] < lm: lm = self[j][3]
                    
        elif high <= self[i-1][2] and low < self[i-1][3]: # downbar
            if i == 1: # only one previous, so this must be an H
                output[0] = H
            elif self[i-1][2] > self[i-2][2] and self[i-1][3] >= self[i-2][3]:
                # previous high bar
                hm, lm = None, None
                for j in range(i-1,-1,-1): # look back for pre-previous high
                    # remember high low range, because if an outer is detected
                    # before the low looping should be stopped and the next 
                    # candle evaluated
                    outer_break = False
                    if not hm or not lm:
                        hm, lm = self[j][2], self[j][3]
                        continue
                    ## this is for outer detection, a difficult but important
                    # problem to tackle 
                    if self[j][2] >= hm and self[j][3] <= lm: # outer detected
                        # now it's important if the current candle is higher or
                        # lower than the outer, the outer should be evaluated for
                        # a top
                        if self[i][2] > self[j][2] or self[i][3] < self[j][3]:
                            for k in range(j-1,-1,-1):
                                outer_break_2 = False
                                if output[k] != 0 and output[k] % 2 == 0:
                                    # high, no problem
                                    outer_break = True
                                    break # and break outer !!!!
                                elif output[k] % 2 == 1: # low
                                    # now the outer is a high
                                    # check what kind of high
                                    # look back further for the next high
                                    for l in range(k-1,-1,-1): 
                                        if output[l] != 0 and output[l] % 2 == 0: # high
                                            if   self[j][2]  < self[l][2]: output[j] = LH
                                            elif self[j][2]  > self[l][2]: output[j] = HH
                                            elif self[j][2] == self[l][2]: output[j] = EH 
                                            else: output[j] = H
                                            outer_break = True
                                            outer_break_2 = True
                                            break
                                if outer_break_2: break
                    if outer_break: break
                    ## end of outer detection block
                    if output[j] != 0 and output[j] % 2 == 0: # high
                        if   self[i-1][2]  < self[j][2]: output[i-1] = LH
                        elif self[i-1][2]  > self[j][2]: output[i-1] = HH
                        elif self[i-1][2] == self[j][2]: output[i-1] = EH 
                        else: output[i-1] = H
                        break
                    if self[j][2] > hm: hm = self[j][2]
                    if self[j][3] < lm: lm = self[j][3]
        
    return TopsWrapper(self, output)    