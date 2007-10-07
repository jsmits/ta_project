from signals import entry_long_random, entry_short_random

class Strategy(object):
    def __init__(self, signal, bracket=(1.00, 1.00)):
        self.signal = signal
        self.bracket = bracket # first index is STOP, second is LIMIT
        self.trigger_tick = None
        
    def check_entry(self, ticker):
        resp = self.signal(ticker)
        # response can be None, False, True, or a bracket tuple
        if resp:
            self.trigger_tick = ticker.ticks[-1]
            # get the dynamic bracket from the response
            if isinstance(resp, tuple):
                self.bracket = resp
            return self
        
    def exit_params(self):
        ref_value = self.trigger_tick.value
        signal_name = self.signal.__name__
        if signal_name.startswith('entry_long'):  
            action = "SELL"
            stop = ref_value - self.bracket[0]
            limit = ref_value + self.bracket[1]
            return action, stop, limit
        elif signal_name.startswith('entry_short'): 
            action = "BUY"
            stop = ref_value + self.bracket[0]
            limit = ref_value - self.bracket[1]
            return action, stop, limit
        
strategy_list = [Strategy(entry_long_random), Strategy(entry_short_random)]
        

                
        