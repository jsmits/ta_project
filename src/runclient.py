from strategies import strategy_1

if __name__ == '__main__':
    
    import stomp
    from ta_engine import TAEngine
    from message_service import MessagingGateway
    from ticker import Ticker
    
    definitions = [
        {'symbol': "ES",
        'secType': "FUT",
        'expiry': "200712",
        'exchange': "GLOBEX",
        'currency': "USD",
        'strategy': strategy_1 
        }
    ]
    
    tickers = {}
    id = 0
    for definition in definitions:
        id += 1
        ticker = Ticker(**definition)
        tickers.update({id: ticker})
    print tickers
    
    try:
        mconn = stomp.Connection([('localhost', 61613)], '', '')
        ta_engine = TAEngine(tickers)
        mconn.add_listener(ta_engine)
        mgw = MessagingGateway(mconn)
        ta_engine.mgw = mgw
        ta_engine.start()
        while True:
            line = raw_input("\r> ")
            if not line or line.lstrip().rstrip() == '':
                continue
            elif 'quit' in line or 'disconnect' in line:
                break
            split = line.split()
            command = split[0]
            if not command.startswith("on_") and hasattr(mgw, command):
                getattr(mgw, command)(split)
            else:
                print 'unrecognized command'
    finally:
        print "-> exit"
        ta_engine.exit()