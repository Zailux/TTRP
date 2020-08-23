Welcome to TTRP's master project documentation!
===============================================

This is the sphinx documentation for the master project Track to reference (TTRP).
The TTRP application implements a electromagnetic guided ultrasound navigation system and
is created within the CaMed Masterprojekt (Computergestützte Medizin) at Reutlingen University.
The current version is based on the work of N. Bach and T. Baader in 2019/2020.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   rst/background
   rst/installation
   rst/architecture
   rst/uvis_app
   rst/aurora_api
   rst/further_reading


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Requirements
============

* Python 3.7.5 or higher
* NDI Aurora system
* Frame Grabber (e.g. Epiphan AV.io frame grabber)
* Ultrasound system


Installation
============

**Short Step-by-Step Guide**
 * Install the Hardware drivers

   * NDI Toolbox + Aurora drivers
   * Epiphan AV.io Framegrabber drivers
 * Setup Python project

   * ``git clone https://github.com/Zailux/TTRP.git <path/to/project>``
   * Setup virtualenv with Python 3.7.5 64 bit (venvdoc_)
   * Install required packages via ``pip install -r requirements.txt``
 * Configure application in ``config.py``
 * Start the ``main.py``



Master project documentation
----------------------------

The project documentation to the several CaMed master projects can be found
in `MS Teams / Sharepoint <https://teams.microsoft.com/l/team/19%3a4858c510b75649868bac202eef5a2518%40thread.tacv2/conversations?groupId=56d866fc-6954-49ae-8ad7-369c751e458d&tenantId=a0629466-5815-4bba-a174-daf8ccaf3be1>`_
of Reutlingen University.

* Peter Grupp 17/18
* Thanh Nam Bach 19/20

.. _venvdoc: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/