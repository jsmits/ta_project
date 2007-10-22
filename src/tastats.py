import pickle

from pptable import indent

class SimStats(object):
    def __init__(self, file_name):
        self.strategies = {}
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
        
    def sort_stats(self, field):
        pass
    
    def print_stats(self, number=None):
        labels= ('id', 'delta', 'orders', 'longs', 'shorts')
        rows = []
        for id, s in self.strategies.items():
            rows.append((str(id), str(s['delta']), str(s['orders']), str(s['longs']), str(s['shorts'])))
        print indent([labels] + rows, hasHeader=True, justify='right') 
    
            