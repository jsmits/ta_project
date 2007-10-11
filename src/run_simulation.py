from datetime import datetime
from simulation import SimulationBot

ticker_map = {
    "ES": {'increment': 0.25, 'commission': 0.1, 'start': datetime(2004, 1, 1),
           'end': datetime(2007, 1, 1), 'hours': ((8,30), (14,45))},
}

if __name__ == '__main__':
    
    import Queue
    from signals import random_strategies_generator
    from tickdata import random_day_generator
    import operator
    
    symbol = "ES"
    ticker_details = ticker_map.get(symbol)
    ticker_details.update({'symbol': symbol})
    
    nr_strategies = 40
    nr_days = 4
    strategy_args = random_strategies_generator(number=nr_strategies) 
    days = random_day_generator(symbol, ticker_details['start'], 
                                        ticker_details['end'], nr_days)
    # -- map --
    print "task dispatching started at %s" % str(datetime.now())
    # create tasks
    tasks = {}
    task_id = 1
    strategy_id = 1
    strategy_results = {}
    for args in strategy_args:
        for day in days:
            task = {'strategy_id': strategy_id, 'strategy_args': args, 
                    'day': day, 'ticker': ticker_details, 'task_id': task_id}
            tasks[task_id] = task
            task_id += 1
        strategy_results[strategy_id] = 0
        strategy_id += 1
        
    # create Queue
    queue = Queue.Queue()
    result = []
    
    # create 2 workers
    for i in range(1):
        bot = SimulationBot(queue, result)
        bot.setDaemon(1)
        bot.start()
    
    # publish the tasks
    for task in tasks.values():
        queue.put(task)
    
    queue.join()
    print "all tasks have been processed at %s" % str(datetime.now())
    
    for result_dict in result:
        for task_id, report in result_dict.items():
            tsk = tasks.get(task_id)
            tsk.update({'report': report})
                
    # -- reduce --
    ## here the key is to get the cumulative delta per strategy and 
    # make a top 5% of strategies
    for id, task in tasks.items():
        strategy_id = task['strategy_id']
        for order_id, order in task['report'].items():
            strategy_results[strategy_id] += order['delta']
            
    strategy_results_list = strategy_results.items()
    strategy_results_list.sort(key=operator.itemgetter(1))
    
    print "results by strategy (ordered by cumulative delta):"
    for (id, delta) in strategy_results_list:
        print id, delta
    print
    
    percentage = 10
    total = len(strategy_results_list)
    if total > percentage:
        print "top 10 % are:"
        print strategy_results_list[-int(total/10):]
        
    
    