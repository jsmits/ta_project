from datetime import datetime
import time

def process_fields(fields):    
    month, day, year = fields[0].split("/")
    hour, minute = fields[1].split(":")
    date = datetime(int(year), int(month), int(day), int(hour), int(minute))
    timestamp = time.mktime(date.timetuple())
    return timestamp, float(fields[2]), float(fields[3]), float(fields[4]), \
                                                        float(fields[5])
                                                        
def parse_line(line):
    if line[-2:] == '\r\n': # always check this first => CPython newline
        line = line[:-2]
    if line[-1:] == '\n': # jython newline
        line = line[:-1]
    fields = line.split(",")
    candle = process_fields(fields)
    return candle

def ES_ticks(start, end):
    #TODO: find the right file for symbol, start and end
    path = '../tickdata/ES/1_Min/'
    f = open(path + 'ES_03U.TXT', 'r')
    title_line = f.readline() # skip first line
    ticks = []
    for line in f.readlines():
        candle = parse_line(line)
        timestamp, o, h, l, c = candle
        date = datetime.fromtimestamp(timestamp)
        if date >= end: break
        if date >= start:
            ticks.append({'timestamp': timestamp-57, 'value': o})
            ticks.append({'timestamp': timestamp-44, 'value': h})
            ticks.append({'timestamp': timestamp-28, 'value': l})
            ticks.append({'timestamp': timestamp- 7, 'value': c})
    f.close()
    return ticks

def handle_temp(data):
    delta = 60.0 / (len(data) + 1)
    timestamp = data[0][0]
    for i in range(len(data)):
        data[i] = timestamp, data[i][1]
        timestamp = timestamp + delta
    return data

def SP_ticks(dt, hist=1):
    ticks = SP_ticks_gen(dt)
    if not ticks: return
    if hist:
        path = '../tickdata/SP/tick/'
        f = open(path + 'SP_05Z.TXT', 'r')
        title_line = f.readline() # skip first line
        previous = None
        for line in f.readlines():
            candle = parse_line(line)
            timestamp, o, h, l, c = candle
            d = datetime.fromtimestamp(timestamp)
            if d.date() == dt.date():
                break
            previous = d
        f.close()
        if previous:
            hist_ticks = SP_ticks_gen(previous)
        ticks = hist_ticks + ticks
    return ticks
        
def SP_ticks_gen(date):
    #TODO: find the right file for symbol, start and end
    path = '../tickdata/SP/tick/'
    f = open(path + 'SP_05Z.TXT', 'r')
    title_line = f.readline() # skip first line
    ticks = []
    first_run = []
    for line in f.readlines():
        candle = parse_line(line)
        timestamp, o, h, l, c = candle
        d = datetime.fromtimestamp(timestamp).date()
        if d == date.date():
            first_run.append((timestamp, o))
    f.close()
    current_time = first_run[0][0]
    tuple_ticks = []
    temp = []
    for i in range(len(first_run)):
        if first_run[i][0] == current_time:
            temp.append(first_run[i])
        else:
            data = handle_temp(temp)
            tuple_ticks.extend(data)
            temp = []
            temp.append(first_run[i])
            current_time = first_run[i][0]
    dict_ticks = []
    for ts, v in tuple_ticks:
        dict_ticks.append({'timestamp': ts, 'value': v})
    return dict_ticks