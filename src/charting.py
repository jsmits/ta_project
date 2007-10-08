import pychartdir
from datetime import datetime, timedelta
#from Indicators import Indicators # file in ~/ta
import os

def num2date(ordinal):
    d = int(ordinal)
    t = round((ordinal - int(ordinal)) * 86400)
    d = datetime.fromordinal(d)
    d += timedelta(seconds=t)
    return d

def timestamp2date(timestamp):
    d = datetime.fromtimestamp(timestamp)
    return d

def date2num(dt):
    d = dt.toordinal()
    if type(dt).__name__ == 'datetime':
        h = dt.hour
        m = dt.minute
        s = dt.second
        sec = h * 3600 + m * 60 + s
        a = float(sec) / 86400
        d += a
    return d

from datetime import datetime, timedelta
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

def tick_list(symbol, start, end):
    #TODO: find the right file for symbol, start and end
    path = '../tickdata/%s/1_Min/'
    f = open(path % symbol + 'ES_03U.TXT', 'r')
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

def make_chart(candles, tops): # data should be candles, tops are calculated via the candles
    
    labels = []
    dates = [timestamp2date(c[0]) for c in candles] 
    for date in dates:
        if date.minute in [0, 30]: labels.append(date.strftime("%H:%M"))
        else: labels.append("-")
            
    openData = [c[1] for c in candles]
    highData = [c[2] for c in candles]
    lowData = [c[3] for c in candles]
    closeData = [c[4] for c in candles]
    
    # scaling ticks, major and minor, bottom and top # TODO: leave
    high = max(highData)
    low = min(lowData)
    delta = high - low
    if delta <= 5: major = 1
    elif delta > 5 and delta <= 10: major = 2
    elif delta > 10: major = 5
    minor = major / 5.0
    bottom = int(low - (low - major) % major)
    if low - bottom < 0.5: bottom = bottom - major
    top = int((high + major) - high % major)
    if top - high < 0.5: top = top + major
    
    x = 650
    y = 450
    c = pychartdir.XYChart(x, y)
    xMargin = 50
    yMargin = 25
    xPlot = x - (2 * xMargin)
    yPlot = y - (yMargin + 75) 
    c.setPlotArea(xMargin, yMargin, xPlot, yPlot).setGridColor(0xA6ADA5, 
                                    0xA6ADA5, 0xDDDDDD, pychartdir.Transparent)
    #c.addTitle("ticker data")
    #c.addText(50, 25, "(c) Global XYZ ABC Company", "GillSans.dfont|3", 12, 
    # 0x4040c0)
    #c.xAxis().setTitle("Jan 2001")
    c.xAxis().setLabelStyle("GillSans.dfont|1", 8, 0x00).setFontAngle(45)
    c.xAxis().setLabels(labels)
    c.xAxis().setTickLength2(-4, -2)
    c.yAxis().setLabelStyle("GillSans.dfont|1", 8, 0x00)
    c.yAxis().setLinearScale(bottom, top, major, minor)
    c.yAxis().setTickLength2(-4, -2) 
    layer = c.addHLOCLayer(highData, lowData, openData, closeData, 0x1D4221)
    layer.setLineWidth(1.5)
    c.layout() 
    # show the tops

    topsd = {1: ("L", -5, 0, "FF0000"), 2: ("H", -6, -11, "00FF00"), 
             11: ("LL", -7, 0, "FF0000"), 12: ("LH", -7, -11, "00FF00"), 
             21: ("EL", -9, 0, "FF0000"), 22: ("EH", -9, -11, "00FF00"), 
             31: ("HL", -9, 0, "FF0000"), 32: ("HH", -9, -11, "00FF00")}
    
    for i in range(len(tops)):
        el = tops[i]
        if el in topsd.keys():
            tx = c.getXCoor(i)
            if el % 2: ty = c.getYCoor(lowData[i])
            else: ty = c.getYCoor(highData[i])
            tx += topsd[el][1]
            ty += topsd[el][2]
            c.addText(tx, ty, "<*size=6,color=0x%s*>%s<*/*>" % (topsd[el][3], 
                                                                topsd[el][0]))

    return c
    
def main(lcs, scs):
    stamp = int(time.time())
    c = make_chart(lcs, lcs.tops().tops)
    filename = "../charts/hloc_%s_long.png" % stamp
    c.makeChart(filename)
    os.system("open -a ViewIt %s" % filename)
    
    onchart = 60
    s_tops = scs.tops().tops
    start = 0
    end = onchart
    count = 1
    while start < len(scs):
        c = make_chart(scs[start:end], s_tops[start:end])
        filename = "../charts/hloc_%s_short_%s.png" % (stamp, count)
        c.makeChart(filename)
        start += onchart
        end += onchart
        if start >= len(scs): break
        if end > len(scs): end = len(scs)
        count += 1
         

if __name__ == '__main__':
    
    from ticker import Ticker
    
    start = datetime(2003, 6, 9)
    end = datetime(2003, 6, 11)
    ticks = tick_list('ES', start, end)
    
    t = Ticker()
    for tick in ticks:
        t.ticks.append(tick)
        
    lcs = t.ticks.cs(15)
    scs = t.ticks.cs(2)
    
    main(lcs, scs)