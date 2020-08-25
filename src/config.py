"""
This module contains the configurations for setting up the uvis application.
Setting correct paths, Logging configurations, serial configs etc.
"""

import logging


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Configuration(metaclass=Singleton):
    """The :class:`Configuration` object contains all the configuration for the Uvis Application.
    one could research alternatives for configs.

    Attributes

    .. attribute:: DEBUG

        `bool` - Sets the debug mode flag for the Uvis App.

    .. attribute:: DATAPATH

        `str` - Sets the path of the data directory.

    .. attribute:: SAVEDIMGPATH

        `str` - Sets the path where the ultrasound images are saved.

    .. attribute:: IMGPATH

        `str` - Sets the path of the image directory. These images are used for the application itself.

    .. attribute:: COM

        `str` - Sets the COM Port for the :class:`Serial` connection of the application (e.g. `'COM8'`).

    .. attribute:: VID_INPUT

        `int` - Index for choosing the video source. See :class:`cv2.VideoCapture` for more details.

    .. attribute:: LOGGER

        `logging.Logger` - The general logger of the uvis application.

    .. attribute:: Q_LOGGER

        :class:`logging.Logger` - The logger for the queue thread.

    """
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
        self.LOGGER = logging.getLogger('uvis_logger')
        self.Q_LOGGER = logging.getLogger('uvis_queue_logger')

        if self.DEBUG:
            self.LOGGER.setLevel(logging.DEBUG)
            self.Q_LOGGER.setLevel(logging.DEBUG)

