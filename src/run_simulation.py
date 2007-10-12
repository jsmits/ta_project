from datetime import datetime
from simulation import SimulationBot
from tickdata import trial_generator

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
    
    nr_strategies = 200
    nr_days = 3
    strategy_args = random_strategies_generator(number=nr_strategies) 
    days = random_day_generator(symbol, ticker_details['start'], 
                                        ticker_details['end'], nr_days)
    # -- map --
    print "task dispatching started at %s" % str(datetime.now())
    # create tasks
    tasks = {}
    task_id = 1
    strategy_id = 0
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
    
    perc = 5
    total = len(strategy_results_list)
    if total > (100/perc):
        print "top %s percent are:" % perc
        print strategy_results_list[-int(total/(100/perc)):]
    
        # check for minimum delta requirement
        mc_strategies = [id for (id, delta) in strategy_results_list 
                         if delta >= ticker_details['increment'] * 3 * nr_days]
        
        print "strategies for Monte Carlo: %s" % len(mc_strategies)
        
        if mc_strategies:
            
            ## Monte Carlo
            # -- map --
            trials_start = datetime(2006, 1, 1)
            trials_end = datetime(2007, 1, 1)
            trials = trial_generator("ES", trials_start, trials_end, 5, 50)
            
            # build tasks and run simulation
            # create tasks
            mc_tasks = {}
            mc_task_id = 1
            mc_strategy_results = {}
            mc_args = [strategy_args[i] for i in mc_strategies]
            for i in mc_strategies:
                args = strategy_args[i]
                mc_trial_id = 0
                for trial in trials:
                    for day in trial:
                        task = {'strategy_id': i, 'strategy_args': args, 
                                'day': day, 'ticker': ticker_details, 
                                'task_id': task_id, 'trial_id': mc_trial_id}
                        mc_tasks[mc_task_id] = task
                        mc_task_id += 1
                    mc_trial_id += 1
                mc_strategy_results[i] = 0
                
            # create Queue
            mc_queue = Queue.Queue()
            mc_result = []
            
            # publish the tasks
            for task in tasks.values():
                mc_queue.put(task)
                
            # create 2 workers
            for i in range(1):
                bot = SimulationBot(mc_queue, mc_result)
                bot.setDaemon(1)
                bot.start()
            
            mc_queue.join()
            print "all tasks have been processed at %s" % str(datetime.now())
            
            # -- reduce --
            
        else:
            print "insufficient results for Monte Carlo"
        
    
    