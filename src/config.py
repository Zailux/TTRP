"""This is the config module.

This module contains program relevant configurations
"""

import logging


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Configuration(metaclass=Singleton):

    def __init__(self):
        self.DEBUG = True

        #Paths
        self.DATAPATH = 'data\\'
        self.SAVEDIMGPATH = 'data/img/'
        self.IMGPATH = "img\\"

        # Serial Configuration
        self.COM = 'COM8'

        #Video Input Configuration
        self.VID_INPUT = 0                      #defaults to 0

        #Logger
        format = "%(asctime)s - %(threadName)s - %(levelname)s | %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
        self.LOGGER = logging.getLogger()


