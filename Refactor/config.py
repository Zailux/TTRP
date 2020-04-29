import logging

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



class Configuration(metaclass=Singleton):

    def __init__(self):

        self.DATAPATH = '..\\data\\'

        # Serial Configuration
        self.COM = None

        format = "%(asctime)s - %(threadName)s|%(levelname)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
        self.LOGGER = None

        self.DEBUGGING = None