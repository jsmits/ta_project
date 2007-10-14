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
    
    nr_strategies = 1000
    strategy_args = random_strategies_generator(number=nr_strategies) 
    
    #sdt = datetime(*ticker_details['start'])
    #edt = datetime(*ticker_details['end'])
    #days = random_day_generator(symbol, sdt, edt, nr_days)
    prev_w, cur_w, next_w = get_random_week_triplet("ES")
    
    # -- map --
    # step 1, get strategies that work in the current week    
    days = cur_w
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
            
    for process in processes:
        process.stop()
    queue = None
    result = None
        
    # step 2, find strategies that work in the previous week    
    days = prev_w
    nr_days = len(days)
    print "step 2 started at %s" % str(datetime.now())
    # create tasks
    ptasks = {}
    task_id = 1
    pstrategy_results = {}
    strategy_id_task_map = {}
    for id in got:
        args = strategy_args[id]
        strategy_id_task_map[id] = []
        for day in days:
            task = {'strategy_id': id, 'strategy_args': args, 
                    'day': day.timetuple()[:3], 'ticker': ticker_details, 
                    'task_id': task_id}
            ptasks[task_id] = task
            strategy_id_task_map[id].append(task_id)
            task_id += 1
        pstrategy_results[id] = 0
        
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    queue.putmany(ptasks.values())
    # create 2 Processes
    processes = []
    for i in range(2):
        p = Process(target=process_func, args=[queue, result])
        p.setStoppable(True)
        p.start()
        processes.append(p)
    
    criterium = nr_days * ticker_details['increment'] * 3 # 'arbitrary' criterium
    pgot = set()
    
    for i in range(len(ptasks)):
        result_dict = result.get()
        for task_id, report in result_dict.items():
            tsk = ptasks.get(task_id)
            tsk.update({'report': report})
            strategy_id = tsk['strategy_id']
            for order_id, order in report.items():
                pstrategy_results[strategy_id] += order['delta']
            strategy_id_task_map[strategy_id].remove(task_id)
            if not strategy_id_task_map[strategy_id]: # no more tasks for this strategy
                print "all tasks for strategy %s evaluated, checking criterium" % strategy_id
                if pstrategy_results[strategy_id] >= criterium:
                    pgot.add(strategy_id)
                    print "strategy %s fullfills criterium" % strategy_id
    print "%s strategies were also eligible in step 2" % len(pgot)
    print "step 2 finished at %s" % str(datetime.now())
            
    for process in processes:
        process.stop()
    queue = None
    result = None
    
    