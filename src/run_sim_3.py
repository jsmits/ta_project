from datetime import datetime
import time
from processing import Process, BufferedQueue, Queue
from signals import random_strategies_generator
from simulation import process_func

ticker_map = {
    "ES": {'increment': 0.25, 'commission': 0.1, 'start': (2007, 1, 1),
           'end': (2007, 3, 1), 'hours': ((8,30), (14,45))},
}

if __name__ == '__main__':
    
    import pickle
    
    start_time = datetime.now()
    
    symbol = "ES"
    ticker_details = ticker_map.get(symbol)
    ticker_details.update({'symbol': symbol})
    
    batch_nr = 50
    wanted_output = 20
    max_batch_runs = 5
    
    strategies_args = []
    ok_strats = set()
    batch_runs = 0
    
    tasks = {}
    strategy_results = {}
    strategy_id_task_map = {}
    
    days = [datetime(2004, 2, 23, 0, 0), 
            datetime(2004, 2, 24, 0, 0), 
            datetime(2004, 2, 25, 0, 0), 
            datetime(2004, 2, 26, 0, 0), 
            datetime(2004, 2, 27, 0, 0),
            
            datetime(2004, 3,  1, 0, 0), 
            datetime(2004, 3,  2, 0, 0), 
            datetime(2004, 3,  3, 0, 0), 
            datetime(2004, 3,  4, 0, 0), 
            datetime(2004, 3,  5, 0, 0),
        
            datetime(2004, 3,  8, 0, 0), 
            datetime(2004, 3,  9, 0, 0), 
            datetime(2004, 3, 10, 0, 0), 
            datetime(2004, 3, 11, 0, 0), 
            datetime(2004, 3, 12, 0, 0),
            
            datetime(2004, 3, 15, 0, 0), 
            datetime(2004, 3, 16, 0, 0), 
            datetime(2004, 3, 17, 0, 0), 
            datetime(2004, 3, 18, 0, 0), 
            datetime(2004, 3, 19, 0, 0),
        ]
            
    criterium = len(days) * ticker_details['increment'] * 2 # ES specific
    
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    
    p1 = Process(target=process_func, args=[queue, result])
    p2 = Process(target=process_func, args=[queue, result])
    p1.setStoppable(True); p2.setStoppable(True)
    p1.start(); p2.start()
    
    while len(ok_strats) != wanted_output and batch_runs < max_batch_runs:
        
        task_id = len(tasks)
        strategy_id = len(strategies_args)
        batch_tasks = []
        batch_args = random_strategies_generator(number=batch_nr, 
                            exclude=strategies_args)
        strategies_args.extend(batch_args) 
    
        # create tasks for this batch
        for args in batch_args:
            strategy_id_task_map[strategy_id] = []
            for day in days:
                task = {'strategy_id': strategy_id, 'strategy_args': args, 
                        'day': day.timetuple()[:3], 'ticker': ticker_details, 
                        'task_id': task_id}
                tasks[task_id] = task
                strategy_id_task_map[strategy_id].append(task_id)
                batch_tasks.append(task)
                task_id += 1
            strategy_results[strategy_id] = 0
            strategy_id += 1
        
        # put the tasks in the queue
        queue.putmany(batch_tasks)
        batch_runs += 1
        print "running batch: %s" % batch_runs
        
        for i in range(len(batch_tasks)):
            result_dict = result.get()
            for task_id, report in result_dict.items():
                tsk = tasks.get(task_id)
                tsk.update({'report': report})
                strategy_id = tsk['strategy_id']
                for order_id, order in report.items():
                    strategy_results[strategy_id] += order['delta']
                strategy_id_task_map[strategy_id].remove(task_id)
                if not strategy_id_task_map[strategy_id]: # no more tasks for this strategy
                    print "all tasks for strategy %s evaluated" % strategy_id
                    if strategy_results[strategy_id] >= criterium:
                        ok_strats.add(strategy_id)
                        print "strategy %s fullfills criterium, result = %s" % (strategy_id, strategy_results[strategy_id])
            if len(ok_strats) == wanted_output: 
                break
        if len(ok_strats) == wanted_output:
            break
        
    p1.stop(); p2.stop()
    p1.join(); p2.join()
    
    # store the pickled tasks in a file for later analysis
    f = open("../simulations/%s" % start_time.strftime("%Y%m%d%H%M%S"), 'w')
    pickle.dump(tasks, f, pickle.HIGHEST_PROTOCOL)
    f.close()
        