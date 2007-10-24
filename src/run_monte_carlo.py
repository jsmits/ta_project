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
            datetime(2004, 2, 23, 0, 0), 
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
            
            datetime(2004, 3, 22, 0, 0), 
            datetime(2004, 3, 23, 0, 0), 
            datetime(2004, 3, 24, 0, 0), 
            datetime(2004, 3, 25, 0, 0), 
            datetime(2004, 3, 26, 0, 0),
            
            datetime(2004, 3, 29, 0, 0), 
            datetime(2004, 3, 30, 0, 0), 
            datetime(2004, 3, 31, 0, 0), 
            datetime(2004, 4,  1, 0, 0), 
            datetime(2004, 4,  2, 0, 0),
            
            datetime(2004, 4,  5, 0, 0), 
            datetime(2004, 4,  6, 0, 0), 
            datetime(2004, 4,  7, 0, 0), 
            datetime(2004, 4,  8, 0, 0), 
            # datetime(2004, 4,  9, 0, 0), # invalid ticks
            
            datetime(2004, 4, 12, 0, 0), 
            datetime(2004, 4, 13, 0, 0), 
            datetime(2004, 4, 14, 0, 0), 
            datetime(2004, 4, 15, 0, 0), 
            datetime(2004, 4, 16, 0, 0),
            
            #datetime(2004, 4, 19, 0, 0), 
            #datetime(2004, 4, 20, 0, 0), 
            #datetime(2004, 4, 21, 0, 0), 
            #datetime(2004, 4, 22, 0, 0), 
            #datetime(2004, 4, 23, 0, 0),
            
            #datetime(2004, 4, 26, 0, 0), 
            #datetime(2004, 4, 27, 0, 0), 
            #datetime(2004, 4, 28, 0, 0), 
            #datetime(2004, 4, 29, 0, 0), 
            #datetime(2004, 4, 30, 0, 0),
            
            #datetime(2004, 5,  3, 0, 0), 
            #datetime(2004, 5,  4, 0, 0), 
            #datetime(2004, 5,  5, 0, 0), 
            #datetime(2004, 5,  6, 0, 0), 
            #datetime(2004, 5,  7, 0, 0),
            
            #datetime(2004, 5, 10, 0, 0), 
            #datetime(2004, 5, 11, 0, 0), 
            #datetime(2004, 5, 12, 0, 0), 
            #datetime(2004, 5, 13, 0, 0), 
            #datetime(2004, 5, 14, 0, 0),
        ]
            
    # create Queues
    queue = BufferedQueue()
    result = Queue()
    
    p1 = Process(target=process_func, args=[queue, result])
    p2 = Process(target=process_func, args=[queue, result])
    p1.setStoppable(True); p2.setStoppable(True)
    p1.start(); p2.start()
    
    strategy_args = random_strategies_generator_2(periods=(1,2,3,4,5,10,15), 
                                                  strats_per_period=20)
    #strategy_args = []
    weeks = random_weeks_generator(days, number=12)
    
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
        