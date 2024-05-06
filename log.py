import logging
import logging.config
import os

LOGGER_NAME = 'honeycomb'

class Logger:
    _instance = None

    def __init__(self, name, log_level=logging.INFO):
        self._app_logger = logging.getLogger(name)
        self._sa_logger = logging.getLogger('sqlalchemy')
        self._app_logger.setLevel(log_level)
        self._sa_logger.setLevel(log_level)

        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s: %(funcName)s \n%(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
            )
        
        stream_handler = logging.StreamHandler() #그냥 handler는 ABC임.
        stream_handler.setFormatter(formatter)
        self._app_logger.addHandler(stream_handler)
        self._sa_logger.addHandler(stream_handler)

        if not os.path.exists('./log'):
            os.makedirs('./log')

        # app log file
        file_handler = logging.FileHandler('./log/app.log')
        file_handler.setFormatter(formatter)
        self._app_logger.addHandler(file_handler)

        # sqlalchemy log file
        sa_file_handler = logging.FileHandler('./log/sqlalchemy.log')
        sa_file_handler.setFormatter(formatter)
        self._sa_logger.addHandler(sa_file_handler)
        # logging.config.fileConfig('logging.config')
    
    def info(self, msg):
        self._app_logger.info(msg)
    
    def error(self, msg):
        self._app_logger.error(msg)

    def debug(self, msg):
        self._app_logger.debug(msg)                

    def get_app_logger(self):
        return self._app_logger
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Logger(LOGGER_NAME)            
        return cls._instance
