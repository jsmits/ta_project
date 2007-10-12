from datetime import datetime
from tickdata import trial_generator
from processing import Process, BufferedQueue, Queue
from simulation import process_func

ticker_map = {
    "ES": {'increment': 0.25, 'commission': 0.1, 'start': (2007, 1, 1),
           'end': (2007, 3, 1), 'hours': ((8,30), (14,45))},
}

if __name__ == '__main__':
    
    from signals import random_strategies_generator
    from tickdata import random_day_generator
    import operator
    
    symbol = "ES"
    ticker_details = ticker_map.get(symbol)
    ticker_details.update({'symbol': symbol})
    
    nr_strategies = 600
    nr_days = 5
    strategy_args = random_strategies_generator(number=nr_strategies) 
    sdt = datetime(*ticker_details['start'])
    edt = datetime(*ticker_details['end'])
    days = random_day_generator(symbol, sdt, edt, nr_days)
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
                    'day': day.timetuple()[:3], 'ticker': ticker_details, 
                    'task_id': task_id}
            tasks[task_id] = task
            task_id += 1
        strategy_results[strategy_id] = 0
        strategy_id += 1
        
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    
    # publish the tasks
    queue.putmany(tasks.values())
    
    # create 2 Processes
    processes = []
    for i in range(2):
        p = Process(target=process_func, args=[queue, result])
        p.setStoppable(True)
        p.start()
        processes.append(p)
    
    for i in range(len(tasks)):
        result_dict = result.get()
        for task_id, report in result_dict.items():
            tsk = tasks.get(task_id)
            tsk.update({'report': report})
    print "all tasks have been processed at %s" % str(datetime.now())
                
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
            
            ## Monte Carlo, small 10 random weeks
            # -- map --
            trials_start = datetime(2006, 1, 1)
            trials_end = datetime(2007, 1, 1)
            trials = trial_generator("ES", trials_start, trials_end, 5, 10)
            
            # build tasks and run simulation
            # create tasks
            mc_tasks = {}
            mc_task_id = 1
            mc_strategy_results = {}
            mc_args = [strategy_args[i] for i in mc_strategies]
            for i in mc_strategies:
                args = strategy_args[i]
                mc_strategy_results[i] = {}
                mc_trial_id = 0
                for trial in trials:
                    for day in trial:
                        mc_strategy_results[i][mc_trial_id] = 0
                        task = {'strategy_id': i, 'strategy_args': args, 
                          'day': day.timetuple()[:3], 'ticker': ticker_details, 
                          'task_id': task_id, 'trial_id': mc_trial_id}
                        mc_tasks[mc_task_id] = task
                        mc_task_id += 1
                    mc_trial_id += 1
            
            # publish the tasks
            queue.putmany(mc_tasks.values())

            print "all tasks have been processed at %s" % str(datetime.now())
            for i in range(len(mc_tasks)):
                result_dict = result.get()
                for task_id, report in result_dict.items():
                    tsk = mc_tasks.get(task_id)
                    tsk.update({'report': report})
                    
            # -- reduce --
            for id, task in mc_tasks.items():
                strategy_id = task['strategy_id']
                for order_id, order in task['report'].items():
                    mc_strategy_results[strategy_id][task['trial_id']] += order['delta']
            
        else:
            print "insufficient results for Monte Carlo"
            
    for process in processes:
        process.stop()
        
    
    