from signals import entry_long_random, entry_short_random

class Strategy(object):
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
        
strategy_list = [Strategy(entry_long_random), Strategy(entry_short_random)]
        

                
        