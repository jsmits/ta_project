if __name__ == '__main__':
    
    import stomp
    from ta_engine import TAEngine
    from message_service import MessagingGateway
    
    try:
        mconn = stomp.Connection([('localhost', 61613)], '', '')
        ta_engine = TAEngine()
        mconn.add_listener(ta_engine)
        mgw = MessagingGateway(mconn)
        ta_engine.mgw = mgw
        connected = ta_engine.start()
        if connected:
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