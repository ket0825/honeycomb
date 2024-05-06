import logging
import logging.config

LOGGER_NAME = 'honeycomb'

class Logger:
    _instance = None

    def __init__(self, name):
        self._logger = logging.getLogger(name)
        logging.config.fileConfig('logging.config')

    def get_logger(self):
        return self._logger
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Logger(LOGGER_NAME)
        return cls._instance
