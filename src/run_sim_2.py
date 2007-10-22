from datetime import datetime
from tickdata import trial_generator
from processing import Process, BufferedQueue, Queue
from simulation import process_func
from signals import random_strategies_generator
from tickdata import get_random_week_triplet, random_day_generator

ticker_map = {
    "ES": {'increment': 0.25, 'commission': 0.1, 'start': (2007, 1, 1),
           'end': (2007, 3, 1), 'hours': ((8,30), (14,45))},
}

if __name__ == '__main__':
    
    symbol = "ES"
    ticker_details = ticker_map.get(symbol)
    ticker_details.update({'symbol': symbol})
    
    strategy_args = [[('long_tops', 3, 'HL', 'HH', 6, 3), 
                      ('long_tops', 10, 'HL', 'high', 5, 7), 
                      ('long_tops', 2, 'HL', 'LH', 8, 6), 
                      ('long_tops', 10, 'LL', 'LH', 5, 7), 
                      ('long_tops', 5, 'HL', 'high', 6, 8), 
                      ('long_tops', 3, 'HL', 'high', 6, 2), 
                      ('long_tops', 2, 'LL', 'high', 2, 6)]]
    #strategy_args = random_strategies_generator(number=nr_strategies) 
    strategy_args = [[#('long_tops_2', 5),
                      ('short_tops', 5, 'high', 'LL', 4, 4)]] 
    
    #prev_w, cur_w, next_w = get_random_week_triplet("ES")
    days = [datetime(2004, 2, 23, 0, 0), 
            #datetime(2004, 2, 24, 0, 0), 
            #datetime(2004, 2, 25, 0, 0), 
            #datetime(2004, 2, 26, 0, 0), 
            #datetime(2004, 2, 27, 0, 0)
            ]
    
    cdays = [datetime(2004, 3, 1, 0, 0), 
            datetime(2004, 3, 2, 0, 0), 
            datetime(2004, 3, 3, 0, 0), 
            datetime(2004, 3, 4, 0, 0), 
            datetime(2004, 3, 5, 0, 0)]
    
    ndays = [datetime(2004, 3, 8, 0, 0), 
            datetime(2004, 3, 9, 0, 0), 
            datetime(2004, 3, 10, 0, 0), 
            datetime(2004, 3, 11, 0, 0), 
            datetime(2004, 3, 12, 0, 0)
            ]
    # -- map --
    # step 1, get strategies that work in the current week    
    nr_days = len(days)
    print "step 1 started at %s" % str(datetime.now())
    # create tasks
    tasks = {}
    task_id = 1
    strategy_id = 0
    strategy_results = {}
    strategy_id_task_map = {}
    for args in strategy_args:
        strategy_id_task_map[strategy_id] = []
        for day in days:
            task = {'strategy_id': strategy_id, 'strategy_args': args, 
                    'day': day.timetuple()[:3], 'ticker': ticker_details, 
                    'task_id': task_id}
            tasks[task_id] = task
            strategy_id_task_map[strategy_id].append(task_id)
            task_id += 1
        strategy_results[strategy_id] = 0
        strategy_id += 1
        
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    queue.putmany(tasks.values())
    # create 2 Processes
    processes = []
    for i in range(2):
        p = Process(target=process_func, args=[queue, result])
        p.setStoppable(True)
        p.start()
        processes.append(p)
    
    wanted = 10
    criterium = nr_days * ticker_details['increment'] * 3 # 'arbitrary' criterium
    got = set()
    
    for i in range(len(tasks)):
        result_dict = result.get()
        for task_id, report in result_dict.items():
            tsk = tasks.get(task_id)
            tsk.update({'report': report})
            strategy_id = tsk['strategy_id']
            for order_id, order in report.items():
                strategy_results[strategy_id] += order['delta']
            strategy_id_task_map[strategy_id].remove(task_id)
            if not strategy_id_task_map[strategy_id]: # no more tasks for this strategy
                print "all tasks for strategy %s evaluated, checking criterium" % strategy_id
                if strategy_results[strategy_id] >= criterium:
                    got.add(strategy_id)
                    print "strategy %s fullfills criterium" % strategy_id
        if len(got) == wanted:
            break
    print "found %s strategies in step 1" % len(got)
    print "step 1 finished at %s" % str(datetime.now())

    queue = None
    result = None            
    for process in processes:
        process.stop()

        
