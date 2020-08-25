Installation
============

Do you have any feedback for the guide? Is anything unclear?
Please contact me <thanh_nam.bach@student.reutlingen-university.de>

Project structure
-----------------

.. image:: imgs/folder.*




Installing the project
----------------------

Drivers
^^^^^^^

Before using the project you need to install the drivers for
NDI Aurora system and the AV.io frame grabber.
The drivers are available in the ``root\docs`` folder.
Alternatively here are the official links

**NDI Aurora System**

.. hint::
    Possibly you need to register at the NDI support portal with your student email. But that is fast.

* NDI Tool Box (https://support.ndigital.com/downloads.php?filetypebrowse=software) - contains necessary tools and drivers for connecting to NDI Aurora System
* NDI User Guide and API Guides (https://github.com/Zailux/TTRP/master/docs/NDI LINK anpassen???) TODO

**Avio Epiphan Framegrabber**

* Official documentation (https://www.epiphan.com/support/avio-hd-software-documentation/)


Python environment
^^^^^^^^^^^^^^^^^^

* Install Python 3.7.5 or higher from https://python.org
* Clone the project with ``git clone https://github.com/Zailux/TTRP.git <path/to/project>``
* Create a clean virtual environment with ``virtualenv``. Please check out `virtualenv documentation`_.
* Install the relevant packages with ``pip install -r requirements.txt``


Starting the application
------------------------
* Configure your application in the ``config.py`` module
    * Configure the ``COM Port`` for serial connection to the NDI Aurora system.
      In Windows you'll find that info under *control panel > device manager > COM devices*.
    * Optionally configure the ``paths`` and ``video input`` of your system. But normally the defaults should suffice.
      If you have a webcam you might need to change the video input to ``1``.
* Start the ``main.py``

.. _virtualenv documentation: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/


