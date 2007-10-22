import pickle

from pptable import indent

def sortfunc_generator(field):
    def sortfunc(x, y):
        if field.startswith("-"):
            field = field[1:]
            sort_args = x[1][field], y[1][field]
        else:
            sort_args = y[1][field], x[1][field]
        return cmp(*sort_args)
    return sortfunc

class SimStats(object):
    def __init__(self, file_name):
        self.strategies = {}
        self.keys = []
        self.valid_sort_fields = ["delta", "orders"]
        f = open(file_name, 'r')
        self.parse_input(pickle.load(f))
        f.close()
            
    def parse_input(self, tasks):
        for task in tasks.values():
            task_id = task['task_id']
            strategy_id = task['strategy_id']
            strategy_args = task['strategy_args']
            strategy = self.strategies.get(strategy_id, {})
            reports = strategy.get('reports', [])
            report = task['report']
            reports.append(report)
            delta = strategy.get('delta', 0)
            total_orders = strategy.get('orders', 0)
            longs = strategy.get('longs', 0)
            shorts = strategy.get('shorts', 0)
            for order_id, order in report.items():
                delta += order['delta']
                total_orders += 1
                signal_args = order['signal']
                sign = signal_args[0]
                if sign.startswith('long'):
                    longs += 1
                if sign.startswith('short'):
                    shorts += 1
            strategy.update({'delta': delta})
            strategy.update({'orders': total_orders, 'longs': longs, 'shorts': shorts})
            strategy.update({'reports': reports})
            strategy.update({'strategy_args': strategy_args})
            self.strategies.update({strategy_id: strategy})
            if strategy_id not in self.keys: 
                self.keys.append(strategy_id)
        
    def sort_stats(self, field):
        if not self.is_valid_sort_field(field):
            raise Exception("invalid sort field: %s" % field)
        items = self.strategies.items()
        sortfunc = sortfunc_generator(field)
        items.sort(sortfunc)
        self.keys = [item[0] for item in items]
        return self
    
    def is_valid_sort_field(self, field):
        if field.startswith("-"): 
            field = field[1:]
        return field in self.valid_sort_fields
    
    def output_generator(self, number):
        keys = self.keys[:number] if number else self.keys
        for key in keys:
            yield key, self.strategies[key]
        self.keys = self.strategies.keys() # reset to original keys
        self.keys.sort()
        
    def print_stats(self, number=None):
        labels= ('id', 'l/s', 'delta', 'orders', 'longs', 'shorts')
        rows = []
        for id, s in self.output_generator(number):
            long_signals = [x for x in s['strategy_args'] if x[0].startswith('long')]
            short_signals = [x for x in s['strategy_args'] if x[0].startswith('short')]
            rows.append((str(id),
                         "%s/%s" % (str(len(long_signals)), str(len(short_signals))), 
                         str(s['delta']), 
                         str(s['orders']), 
                         str(s['longs']), 
                         str(s['shorts'])))
        print indent([labels] + rows, hasHeader=True, justify='right')
        
    def print_details(self, key):
        pass
    
            