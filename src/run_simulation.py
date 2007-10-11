from datetime import datetime
from simulation import SimulationBot
import time

ticker_map = {
    "ES": {'increment': 0.25, 'commission': 0.1, 'start': datetime(2004, 1, 1),
           'end': datetime(2007, 1, 1), 'hours': ((8,30), (14,45))},
}

if __name__ == '__main__':
    
    import Queue
    from signals import random_strategies_generator
    from tickdata import random_day_generator
    
    symbol = "ES"
    ticker_details = ticker_map.get(symbol)
    ticker_details.update({'symbol': symbol})
    
    nr_strategies = 5
    nr_days = 2
    strategy_args = random_strategies_generator(number=nr_strategies) 
    days = random_day_generator(symbol, ticker_details['start'], 
                                        ticker_details['end'], nr_days)
    # -- map --
    # create tasks
    tasks = {}
    task_id = 1
    strategy_id = 1
    remaining_tasks = []
    for args in strategy_args:
        for day in days:
            task = {'strategy_id': strategy_id, 'strategy_args': args, 
                    'day': day, 'ticker': ticker_details, 'task_id': task_id}
            tasks[task_id] = task
            remaining_tasks.append(task_id)
            task_id += 1
        strategy_id += 1
        
    # create Queue
    queue = Queue.Queue()
    result = []
    
    # create 2 workers
    for i in range(2):
        bot = SimulationBot(queue, result)
        bot.setDaemon(1)
        bot.start()
    
    # publish the tasks
    for task in tasks.values():
        queue.put(task)
    
    queue.join()
    
    for result_dict in result:
        for task_id, report in result_dict.items():
            tsk = tasks.get(task_id)
            try:
                remaining_tasks.remove(task_id)
            except ValueError:
                continue
            else:
                tsk.update({'report': report})
                
    # -- reduce --
    