from datetime import datetime
from processing import Process, BufferedQueue, Queue
from simulation import process_func
from signals import random_strategies_generator_2
from signals import random_weeks_generator

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
    
    days = [
            datetime(2004, 5, 17, 0, 0), 
            datetime(2004, 5, 18, 0, 0), 
            datetime(2004, 5, 19, 0, 0), 
            datetime(2004, 5, 20, 0, 0), 
            datetime(2004, 5, 21, 0, 0),
            
            datetime(2004, 5, 24, 0, 0), 
            datetime(2004, 5, 25, 0, 0), 
            datetime(2004, 5, 26, 0, 0), 
            datetime(2004, 5, 27, 0, 0), 
            datetime(2004, 5, 28, 0, 0),
            
            ##!datetime(2004, 5, 31, 0, 0)!, # unavailable
            datetime(2004, 6,  1, 0, 0), 
            datetime(2004, 6,  2, 0, 0), 
            datetime(2004, 6,  3, 0, 0), 
            datetime(2004, 6,  4, 0, 0),
            
            datetime(2004, 6,  7, 0, 0), 
            datetime(2004, 6,  8, 0, 0), 
            datetime(2004, 6,  9, 0, 0), 
            datetime(2004, 6, 10, 0, 0), 
            ##!datetime(2004, 6, 11, 0, 0)!, # unavailable
            
            datetime(2004, 6, 14, 0, 0), 
            datetime(2004, 6, 15, 0, 0), 
            datetime(2004, 6, 16, 0, 0), 
            datetime(2004, 6, 17, 0, 0), 
            datetime(2004, 6, 18, 0, 0),
            
            datetime(2004, 6, 21, 0, 0), 
            datetime(2004, 6, 22, 0, 0), 
            datetime(2004, 6, 23, 0, 0), 
            datetime(2004, 6, 24, 0, 0), 
            datetime(2004, 6, 25, 0, 0),
            
            #datetime(2004, 6, 28, 0, 0), 
            #datetime(2004, 6, 29, 0, 0), 
            #datetime(2004, 6, 30, 0, 0), 
            #datetime(2004, 7,  1, 0, 0), 
            #datetime(2004, 7,  2, 0, 0),
            
            ##!datetime(2004, 7,  5, 0, 0)!, # unavailable
            #datetime(2004, 7,  6, 0, 0), 
            #datetime(2004, 7,  7, 0, 0), 
            #datetime(2004, 7,  8, 0, 0), 
            #datetime(2004, 7,  9, 0, 0),
            
            #datetime(2004, 7, 12, 0, 0), 
            #datetime(2004, 7, 13, 0, 0), 
            #datetime(2004, 7, 14, 0, 0), 
            #datetime(2004, 7, 15, 0, 0), 
            #datetime(2004, 7, 16, 0, 0),
            
            #datetime(2004, 7, 19, 0, 0), 
            #datetime(2004, 7, 20, 0, 0), 
            #datetime(2004, 7, 21, 0, 0), 
            #datetime(2004, 7, 22, 0, 0), 
            #datetime(2004, 7, 23, 0, 0),
            
            #datetime(2004, 7, 26, 0, 0), 
            #datetime(2004, 7, 27, 0, 0), 
            #datetime(2004, 7, 28, 0, 0), 
            #datetime(2004, 7, 29, 0, 0), 
            #datetime(2004, 7, 30, 0, 0),
            
            #datetime(2004, 8,  2, 0, 0), 
            #datetime(2004, 8,  3, 0, 0), 
            #datetime(2004, 8,  4, 0, 0), 
            #datetime(2004, 8,  5, 0, 0), 
            #datetime(2004, 8,  6, 0, 0),
            
            #datetime(2004, 8,  9, 0, 0), 
            #datetime(2004, 8, 10, 0, 0), 
            #datetime(2004, 8, 11, 0, 0), 
            #datetime(2004, 8, 12, 0, 0), 
            #datetime(2004, 8, 13, 0, 0),
        ]
            
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    
    p1 = Process(target=process_func, args=[queue, result])
    p2 = Process(target=process_func, args=[queue, result])
    p1.setStoppable(True); p2.setStoppable(True)
    p1.start(); p2.start()
    
    #strategy_args = random_strategies_generator_2(periods=(1,2,3,4,5,10,15), 
    #                                              strats_per_period=20)
    strategy_args = [
        (('long_tops', 1, 'low', 'HH', 5, 3), ('short_tops', 1, 'high', 'LL', 5, 3)),
        (('long_tops', 1, 'low', 'HH', 4, 3), ('short_tops', 1, 'high', 'LL', 4, 3)),
        (('long_tops', 1, 'low', 'HH', 8, 3), ('short_tops', 1, 'high', 'LL', 8, 3)),
        (('long_tops', 10, 'low', 'HH', 6, 3), ('short_tops', 10, 'high', 'LL', 6, 3)),
        (('long_tops', 15, 'low', 'HH', 6, 3), ('short_tops', 15, 'high', 'LL', 6, 3)),
        (('long_tops', 15, 'low', 'HH', 8, 3), ('short_tops', 15, 'high', 'LL', 8, 3)),
        (('long_tops', 15, 'low', 'HH', 2, 8), ('short_tops', 15, 'high', 'LL', 2, 8))
    ]
    weeks = random_weeks_generator(days, number=40)
    
    # create tasks for this batch
    trials = []
    for trial in range(len(weeks)):
        print "%s: running trial %s of %s" % (str(datetime.now()), trial+1, len(weeks))
        tasks = {}
        task_id = 0
        days = weeks[trial]
        for i in range(len(strategy_args)):
            args = strategy_args[i]
            for day in days:
                task = {'strategy_id': i, 'strategy_args': args, 
                        'day': day.timetuple()[:3], 'ticker': ticker_details, 
                        'task_id': task_id}
                tasks[task_id] = task
                task_id += 1
    
        # put the tasks in the queue
        queue.putmany(tasks.values())
        print "%s: start analyzing %s tasks" % (str(datetime.now()), len(tasks))
        
        for i in range(len(tasks)):
            result_dict = result.get()
            for task_id, report in result_dict.items():
                tsk = tasks.get(task_id)
                tsk.update({'report': report})
                print "analyzed task: %s" % task_id
        
        trials.append(tasks)
        
    p1.stop(); p2.stop()
    p1.join(); p2.join()
    
    # store the pickled tasks in a file for later analysis
    fname = "../simulations/mc_%s" % start_time.strftime("%Y%m%d%H%M%S")
    f = open(fname, 'w')
    pickle.dump(trials, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    print "output written to: %s" % fname
        