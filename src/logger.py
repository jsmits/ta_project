import logging
import logging.handlers

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

trh = logging.handlers.RotatingFileHandler('../log/ta.log', 'a', 10 * 1024 * 1024, 10)
trh.setLevel(logging.DEBUG)
trh.setFormatter(formatter)

# add handler to stomp.py logger
logger_A = logging.getLogger("stomp.py")
logger_A.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger_A.addHandler(ch)
logger_A.addHandler(trh)

# add handler to messaging logger
mlogger = logging.getLogger("messaging")
mlogger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
mlogger.addHandler(ch)
mlogger.addHandler(trh)

# configure server Logger
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
server_logger.addHandler(ch)
server_logger.addHandler(trh)

# configure server Logger
client_logger = logging.getLogger("client")
client_logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
client_logger.addHandler(ch)
client_logger.addHandler(trh)