import logger # configure the loggers

if __name__ == '__main__':
    
    import stomp
    from tws_service import TWSEngine
    from message_service import MessagingGateway
    
    try:
        mconn = stomp.Connection([('localhost', 61613)], '', '')
        trading_engine = TWSEngine()
        mconn.add_listener(trading_engine)
        mgw = MessagingGateway(mconn)
        trading_engine.mgw = mgw
        trading_engine.start()
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
        trading_engine.exit()