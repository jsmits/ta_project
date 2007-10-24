import pickle

from pptable import indent

def sortfunc_generator(field):
    def sortfunc_reverse(x, y):
        return cmp(x[1][field[1:]], y[1][field[1:]])
    def sortfunc(x, y):
        return cmp(y[1][field], x[1][field])
    if field.startswith("-"):
        return sortfunc_reverse
    else:
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
            delta = strategy.get('delta', 0)
            total_orders = strategy.get('orders', 0)
            longs = strategy.get('longs', 0)
            shorts = strategy.get('shorts', 0)
            report = task.get('report')
            if report:
                reports.append(report)
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
        
    def print_args(self, id):
        strategy = self.strategies.get(id)
        if strategy:
            print strategy['strategy_args']
        
    def print_details(self, key):
        pass
    
class MCStats(object):
    def __init__(self, file_name):
        self.metadata = {}
        self.keys = []
        self.valid_sort_fields = ["min_delta", "max_delta", "avg_delta"]
        f = open(file_name, 'r')
        self.parse_input(pickle.load(f))
        f.close()
            
    def parse_input(self, trials):
        for tasks in trials: 
            strategies = {}
            for task in tasks.values():
                task_id = task['task_id']
                strategy_id = task['strategy_id']
                strategy_args = task['strategy_args']
                strategy = strategies.get(strategy_id, {})
                reports = strategy.get('reports', [])
                delta = strategy.get('delta', 0)
                total_orders = strategy.get('orders', 0)
                longs = strategy.get('longs', 0)
                shorts = strategy.get('shorts', 0)
                report = task.get('report')
                if report:
                    reports.append(report)
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
                strategies.update({strategy_id: strategy})
            
            for id, st in strategies.items():
                md = self.metadata.get(id, {})
                sl = md.get('strategies', [])
                sl.append(st)
                md.update({'strategies': sl})
                self.metadata.update({id: md})
                if id not in self.keys: 
                    self.keys.append(id)
        
        for id, md in self.metadata.items():
            sl = md.get('strategies')
            delta_list  = []
            orders_list = []
            longs_list  = []
            shorts_list = []
            for ss in sl:
                delta_list.append(ss['delta'])
                orders_list.append(ss['orders'])
                longs_list.append(ss['longs'])
                shorts_list.append(ss['shorts'])
            md['min_delta'] = min(delta_list)
            md['max_delta'] = max(delta_list)
            md['avg_delta'] = (sum(delta_list)*1.0)/len(delta_list)
            md['min_orders'] = min(orders_list)
            md['max_orders'] = max(orders_list)
            md['avg_orders'] = (sum(orders_list)*1.0)/len(orders_list)
            md['min_longs'] = min(longs_list)
            md['max_longs'] = max(longs_list)
            md['avg_longs'] = (sum(longs_list)*1.0)/len(longs_list)
            md['min_shorts'] = min(shorts_list)
            md['max_shorts'] = max(shorts_list)
            md['avg_shorts'] = (sum(shorts_list)*1.0)/len(shorts_list)
            
    def sort_stats(self, field):
        if not self.is_valid_sort_field(field):
            raise Exception("invalid sort field: %s" % field)
        items = self.metadata.items()
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
            yield key, self.metadata[key]
        self.keys = self.metadata.keys() # reset to original keys
        self.keys.sort()
        
    def print_stats(self, number=None):
        labels= ('id', 'trials', 'min_delta', 'max_delta', 'avg_delta')
        rows = []
        for id, md in self.output_generator(number):
            rows.append((str(id),
                         str(len(md['strategies'])), 
                         str(md['min_delta']), 
                         str(md['max_delta']), 
                         str(md['avg_delta'])))
        print indent([labels] + rows, hasHeader=True, justify='right')
        
    def print_args(self, id):
        md = self.metadata.get(id)
        if md:
            strategies = md['strategies']
            s0 = strategies[0]
            print s0['strategy_args']
        
    
            