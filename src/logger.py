import logging
import logging.handlers

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.handlers.RotatingFileHandler('../log/ta.log', 'a', 100 * 1024 * 1024, 10)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

# add handler to stomp.py logger
logger_A = logging.getLogger("stomp.py")
logger_A.setLevel(logging.INFO)
logger_A.addHandler(ch)
logger_A.addHandler(fh)

# add handler to messaging logger
mlogger = logging.getLogger("messaging")
mlogger.setLevel(logging.INFO)
mlogger.addHandler(ch)
mlogger.addHandler(fh)

# configure server Logger
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.DEBUG)
server_logger.addHandler(ch)
server_logger.addHandler(fh)

# configure server Logger
client_logger = logging.getLogger("client")
client_logger.setLevel(logging.DEBUG)
client_logger.addHandler(ch)
client_logger.addHandler(fh)