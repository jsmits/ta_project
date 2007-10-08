import logger # configure the loggers
from signals import SignalWrapper, entry_long_random, entry_short_random

if __name__ == '__main__':
    
    import stomp
    from ta_engine import TAEngine
    from message_service import MessagingGateway
    from ticker import Ticker
    
    strategy = [SignalWrapper(entry_long_random), 
                SignalWrapper(entry_short_random)]
    definitions = [
        {'symbol': "ES",
        'secType': "FUT",
        'expiry': "200712",
        'exchange': "GLOBEX",
        'currency': "USD",
        'strategy': strategy,
        'increment': 0.25,
        'quantity': 1
        }
    ]
    
    tickers = {}
    id = 0
    for definition in definitions:
        id += 1
        ticker = Ticker(**definition)
        tickers.update({id: ticker})
    
    try:
        mconn = stomp.Connection([('localhost', 61613)], '', '')
        ta_engine = TAEngine(tickers)
        mconn.add_listener(ta_engine)
        mgw = MessagingGateway(mconn)
        ta_engine.mgw = mgw
        ta_engine.start()
        command_service = ta_engine
        while True:
            line = raw_input("\r> ")
            if not line or line.lstrip().rstrip() == '':
                continue
            elif 'quit' in line or 'disconnect' in line:
                break
            split = line.split()
            command = split[0]
            cmethod = "cl_%s" % command
            if hasattr(command_service, cmethod):
                try:
                    getattr(command_service, cmethod)(split)
                except Exception, e:
                    print "command '%s' failed: %s" % (command, e)
            else:
                print 'unrecognized command'
    finally:
        print "-> exit"
        ta_engine.exit()