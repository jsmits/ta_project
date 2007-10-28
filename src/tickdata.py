from datetime import datetime, timedelta
from calendar import Calendar
import time
import random
import os

cache = {}

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
    return fields

def process_line(line):
    fields = parse_line(line)
    candle = process_fields(fields)
    return candle

def ES_ticks_old(start, end):
    #TODO: find the right file for symbol, start and end
    path = '../tickdata/ES/1_Min/'
    f = open(path + 'ES_03U.TXT', 'r')
    title_line = f.readline() # skip first line
    ticks = []
    for line in f.readlines():
        candle = process_line(line)
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

def analyze_ES_files():
    import os
    output = []
    path = '../tickdata/anfutures/ES/'
    for file in os.listdir(path):
        f = open(file, 'r')
        for line in f.readlines():                    
            if line: output.append(line)
        f.close()
        print "file: %s, start: %s, end: %s" % (file, output[0][:-2], output[-1][:-2])
        output = []
        
ES_files_map = {
    "ES0303TK.CSV": (datetime(2002, 12, 11), datetime(2003,  3, 12)), 
    "ES0306TK.CSV": (datetime(2003,  3, 12), datetime(2003,  6, 11)),
    "ES0309TK.CSV": (datetime(2003,  6, 11), datetime(2003,  9, 10)),
    "ES0312TK.CSV": (datetime(2003,  9, 10), datetime(2003, 12, 10)),
    "ES0403TK.CSV": (datetime(2003, 12, 10), datetime(2004,  3, 10)),
    "ES0406TK.CSV": (datetime(2004,  3, 10), datetime(2004,  6,  9)),
    "ES0409TK.CSV": (datetime(2004,  6,  9), datetime(2004,  9,  8)),
    "ES0412TK.CSV": (datetime(2004,  9,  8), datetime(2004, 12,  8)),
    "ES0503TK.CSV": (datetime(2004, 12,  8), datetime(2005,  3,  9)),
    "ES0506TK.CSV": (datetime(2005,  3,  9), datetime(2005,  6,  8)),
    "ES0509TK.CSV": (datetime(2005,  6,  8), datetime(2005,  9,  7)),
    "ES0512TK.CSV": (datetime(2005,  9,  7), datetime(2005, 12,  7)),
    "ES0603TK.CSV": (datetime(2005, 12,  7), datetime(2006,  3,  8)),
    "ES0606TK.CSV": (datetime(2006,  3,  8), datetime(2006,  6,  7)),
    "ES0609TK.CSV": (datetime(2006,  6,  7), datetime(2006,  9,  6)),
    "ES0612TK.CSV": (datetime(2006,  9,  6), datetime(2006, 12,  6)),
    "ES0703TK.CSV": (datetime(2006, 12,  6), datetime(2007,  3,  7)),
    "ES0706TK.CSV": (datetime(2007,  3,  7), datetime(2007,  6,  6)),
    "ES0709TK.CSV": (datetime(2007,  6,  6), datetime(2007,  9, 12)),
    # append new ES tick files from anfutures.com here
}

def get_unavailable_dates(symbol):
    ua_dict = {
        "ES": [
               datetime(2002, 12, 25, 0, 0), 
               datetime(2003, 1, 1, 0, 0), 
               datetime(2003, 4, 18, 0, 0), 
               datetime(2003, 7, 4, 0, 0), 
               datetime(2003, 12, 25, 0, 0), 
               datetime(2004, 1, 1, 0, 0), 
               datetime(2004, 4, 9, 0, 0), 
               datetime(2004, 5, 31, 0, 0), # data missing between 10:30 and 17:00
               datetime(2004, 6, 11, 0, 0), 
               datetime(2004, 7, 5, 0, 0), # data missing between 10:30 and 17:00
               datetime(2004, 12, 24, 0, 0), 
               datetime(2005, 3, 25, 0, 0),
               datetime(2005, 7, 4, 0, 0), # data missing between 10:30 and 17:00
               datetime(2006, 1, 2, 0, 0), # found manually, starts at 17:00:00
               datetime(2006, 4, 14, 0, 0), 
               datetime(2006, 12, 25, 0, 0), 
               datetime(2007, 1, 1, 0, 0), 
               datetime(2007, 1, 2, 0, 0), # data missing between 8:15 and 15:30
               datetime(2007, 1, 15, 0, 0), # data missing between 10:30 and 17:00
               # add here if there are new files
               # last one scanned was ES0709TK.CSV with unavailable_day_finder
               ]
        }
    ua = ua_dict.get(symbol, [])
    return ua

def is_unavailable(symbol, date):
    ua = get_unavailable_dates(symbol)
    if ua and date in ua: 
        return True
    
def ES_file(dt):
    files_map = ES_files_map
    file_path = '../tickdata/anfutures/ES/'
    for file_name, (start, end) in files_map.items():
        if dt > start and dt <= end: 
            return open(file_path + file_name, 'r')
        
def ES_ticks(date):
    f = ES_file(date)
    if not f: return
    raw_ticks = []
    dd_str = date.strftime("%y%m%d")
    match_str = "ES,%s" % dd_str
    for line in f.readlines():
        if line.startswith(match_str):
            symbol, d, t, value, vol = parse_line(line)
            raw_ticks.append((d, t, value))
        elif len(raw_ticks): 
            break
    f.close()
    raw_ticks_cleaned = clean_ES_ticks(raw_ticks)
    ticks = time_ticks(raw_ticks_cleaned)
    return ticks

def clean_ES_ticks(raw_ticks):
    last_date = None
    last_value = None
    clean_ticks = []
    for d, t, v in raw_ticks:
        if (d,t) == last_date and v == last_value: continue
        else:
            clean_ticks.append((d, t, v))
            last_date = (d, t)
            last_value = v
    return clean_ticks

def time_ticks(raw_ticks):
    ticks = []
    for d, t, v in raw_ticks:
        date = datetime.strptime("%s %s" % (d, t), "%y%m%d %H%M%S")
        tm = time.mktime(date.timetuple())
        ticks.append({'timestamp': tm, 'value': float(v)})
    return ticks

def SP_file(dt):
    year = dt.year
    month = dt.month
    day = dt.day
    m = ''
    if (month == 12 and day > 12) or month == 1 or month == 2 or \
        (month == 3 and day <= 12): m = "H"
    elif (month == 3 and day > 12) or month == 4 or month == 5 or \
        (month == 6 and day <= 12): m = "M"
    elif (month == 6 and day > 12) or month == 7 or month == 8 or \
        (month == 9 and day <= 12): m = "U"
    elif (month == 9 and day > 12) or month == 10 or month == 11 or \
        (month == 12 and day <= 12): m = "Z"
    if not m: return
    path = '../tickdata/price-data/SP/tick/'
    file_name = "SP_%s%s.TXT" % (str(year)[-2:], m)
    print "looking for data in %s" % file_name
    try:
        f = open(path + file_name, 'r')
        return f
    except IOError:
        print "%s not found" % file_name
        return

def SP_ticks(dt, hist=1):
    ticks = SP_ticks_gen(dt)
    if not ticks: return
    if hist:
        f = SP_file(dt)
        if not f: return
        title_line = f.readline() # skip first line
        previous = None
        for line in f.readlines():
            candle = process_line(line)
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
    f = SP_file(date)
    if not f: return
    title_line = f.readline() # skip first line
    ticks = []
    first_run = []
    for line in f.readlines():
        candle = process_line(line)
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

def weekdays_generator(start, end):
    weekdays = []
    current = start
    while current <= end:
        if current.isoweekday() in [1,2,3,4,5]:  
            weekdays.append(current)
        current = current + timedelta(days=1)
    return weekdays

def random_weekday(start, end):
    weekdays = weekdays_generator(start, end)
    if weekdays: 
        return random.choice(weekdays)
    
def random_weekdays(start, end, number=3):
    weekdays = []
    tries = 0
    while len(weekdays) != number:
        weekday = random_weekday(start, end)
        if weekday not in weekdays: 
            weekdays.append(weekday)
        tries += 1
        if tries == 10000: 
            break
    return weekdays

def get_ticks(symbol, day):
    ticks_loader = globals().get("%s_ticks" % symbol)
    ticks = ticks_loader(day)
    return ticks

def get_ticks_2(symbol, day_tuple):
    ticks_path = "/Volumes/MaxiHD/data/ticks"
    year, month, day = day_tuple
    date = datetime(*day_tuple)
    file_name = "%s.txt" % date.strftime("%Y%m%d")
    full_file_name = os.path.join(ticks_path, symbol, file_name)
    ticks = cache.get(full_file_name) or []
    if ticks: return ticks
    try:
        f = open(full_file_name, 'r')
        for line in f.readlines():
            ts, vs = line.strip("\n").strip("\r").split(",")
            hour, minute, second = int(ts[:2]), int(ts[2:4]), int(ts[4:])
            date = datetime(year, month, day, hour, minute, second)
            timestamp = time.mktime(date.timetuple())
            ticks.append({'timestamp': timestamp, 'value': float(vs)})
        f.close()
        cache.update({full_file_name: ticks})
        return ticks
    except IOError, info:
        print "error getting ticks for symbol %s (day: %r) -> %s" % (symbol, day_tuple, info)

def random_day_generator(symbol, start, end, number):
    output = []
    while len(output) != number:
        day = random_weekday(start, end)
        ticks = get_ticks(symbol, day)
        if ticks: # TODO: think about validating these ticks
            output.append(day)
    return output

def trial_generator(symbol, start, end, days, trials):
    output = []
    invalid_days = set([d for d in get_unavailable_dates(symbol)])
    tries = 0
    while len(output) != trials:
        invalid = False
        weekdays = random_weekdays(start, end, number=days)
        weekdays.sort()
        if weekdays not in output:
            for weekday in weekdays:
                if weekday in invalid_days:
                    invalid = True
                    break
            if invalid:
                continue
            else:
                output.append(weekdays)
        tries += 1
        if tries == 100 * trials: 
            break
    return output

def get_random_week_triplet(symbol):
    invalid_days = set([d for d in get_unavailable_dates(symbol)])
    year = random.choice([2003,2004,2005,2006])
    cal = Calendar()
    year_weeks = []
    for month in range(12):
        weeks = cal.monthdatescalendar(year, month+1)
        for week in weeks:                    
            if week not in year_weeks: 
                year_weeks.append(week)
    rwi = random.choice(range(len(year_weeks)-2))
    prev_w, cur_w, next_w = year_weeks[rwi][:5], year_weeks[rwi+1][:5], year_weeks[rwi+2][:5]
    prev_w = [datetime(d.year, d.month, d.day) for d in prev_w]
    cur_w = [datetime(d.year, d.month, d.day) for d in cur_w]
    next_w = [datetime(d.year, d.month, d.day) for d in next_w]
    prev_w = [d for d in prev_w if d not in invalid_days]
    cur_w = [d for d in cur_w if d not in invalid_days]
    next_w = [d for d in next_w if d not in invalid_days]
    return prev_w, cur_w, next_w

def unavailable_day_finder(symbol, start, end):
    unavailable_days = []
    days = weekdays_generator(start, end)
    for day in days:
        ticks = get_ticks(symbol, day)
        if not ticks:
            print "%s unavailable" % str(day)
            unavailable_days.append(day)
    return unavailable_days

def create_tick_files(symbol, start, end, path=None):
    days = weekdays_generator(start, end)
    path = path or "../tickdata/anfutures/ES/perday"
    for day in days:
        ticks = get_ticks(symbol, day)
        if ticks:
            f = open("%s/%s.txt" % (path, day.strftime("%Y%m%d"), 'w'))
            lines = []
            for tick in ticks:
                timestamp = tick['timestamp']
                value = str(tick['value'])
                ts = datetime.fromtimestamp(timestamp).strftime("%H%M%S")
                line = "%s,%s\n" % (ts, value)
                lines.append(line)
            if lines: f.writelines(lines)
            f.close()

if __name__ == '__main__':
    
    from datetime import datetime
    start = datetime(2002, 12, 11)
    end = datetime(2007,  9, 12)
    days = weekdays_generator(start, end)
    path = "../tickdata/anfutures/ES/day"
    
    for day in days:
        ticks = get_ticks("ES", day)
        if ticks:
            f = open("../tickdata/anfutures/ES/perday/%s.txt" % day.strftime("%Y%m%d"), 'w')
            print "ES ticks found for %s" % str(day)
            lines = []
            for tick in ticks:
                timestamp = tick['timestamp']
                value = str(tick['value'])
                ts = datetime.fromtimestamp(timestamp).strftime("%H%M%S")
                line = "%s,%s\n" % (ts, value)
                lines.append(line)
            if lines: f.writelines(lines)
            f.close()
    
    #trials = trial_generator("ES", start, end, 5, 100)
    #prev_w, cur_w, next_w = get_random_week_triplet("ES")
        
    