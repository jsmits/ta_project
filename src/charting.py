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

def chart(data): # data should be candles, tops are calculated via the candles
    m = Indicators()
    tops = m.tops((data[2], data[3]))
    labels = []
    dates = list(data[0])
    
    # determine interval
    fd = num2date(dates[0])
    ed = num2date(dates[-1])
    days = (ed - fd).days
    adpe = float(days) / len(dates)
    if adpe >=1 and adpe <= 2: interval = "D"
    elif adpe >=5 and adpe <= 7: interval = "W"
    elif adpe >= 28 and adpe <= 31: interval = "M"
    if adpe < 1: # intraday data
        secs = (ed - fd).seconds
        adpe = float(secs) / len(dates)
        interval = int(round(adpe / 60))
        
    dati = [num2date(d) for d in dates] 
    if interval == "D":
        for dt in dati:
            if dt.isocalendar()[2] != 1: dt = "-"
            else: dt = dt.strftime("%Y-%m-%d")
            labels.append(dt)
    if interval == "W":
        for dt in dati:
            if dt.day <= 7: dt = dt.strftime("%Y-%m-%d") # first week of month
            else: dt = "-"
            labels.append(dt)
    if interval == "M":
        for dt in dati:
            if dt.month in [1,4,7,10]: dt = dt.strftime("%Y-%m-%d") # quarterly
            else: dt = "-"
            labels.append(dt)
    if type(interval) is int:
        for dt in dati:
            if dt.minute in [0, 30]: dt = dt.strftime("%H:%M")
            else: dt = "-"
            labels.append(dt)
            
    openData = list(data[1])
    highData = list(data[2])
    lowData = list(data[3])
    closeData = list(data[4])
    volData = list(data[5])
    
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
    
    # check missing values # TODO: remove (only for interval D)
    begin = dati[0]
    end = dati[-1]
    count = 0
    current = begin
    if interval == "D":
        while current <= end:
            current += timedelta(days=1)
            if current.weekday() < 5:
                count += 1
                if current not in dati: # missing value
                    if current.weekday() == 0: # monday
                        labels.insert(count, current.strftime("%Y-%m-%d"))
                    else: labels.insert(count, "-")
                    openData.insert(count, pychartdir.NoValue)
                    highData.insert(count, pychartdir.NoValue)
                    lowData.insert(count, pychartdir.NoValue)
                    closeData.insert(count, pychartdir.NoValue)
                    tops.insert(count, pychartdir.NoValue)

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
    c.makeChart("hloci.png")
    os.system("open -a ViewIt hloci.png")
    return dati, labels, openData, highData, lowData, closeData, tops 

