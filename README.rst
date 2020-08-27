========================================================
 TTRP - Track to Reference Ultrasound navigation project
========================================================

Overview
========
This is the code repository of the TTRP master project.

- Project Homepage: https://github.com/Zailux/TTRP/


Version
=======
v1.0 - Thanh Nam Bach 2019-2020


Documentation
=============
For API documentation, usage and examples see files in the "documentation"
directory.  The ".rst" files can be read in any text editor or being converted to
HTML or PDF using Sphinx_. An HTML version is online at
https://ttrp.readthedocs.io/


Installation
============

**Short Step-by-Step Guide**
 * Install the Hardware drivers

   * NDI Toolbox + Aurora drivers
   * Avio Epiphan Framegrabber drivers
 * Setup Python project

   * ``git clone https://github.com/Zailux/TTRP.git <path/to/project>``
   * Setup virtualenv with Python 3.7.5 64 bit (venvdoc_)
   * Install required packages via ``pip install -r requirements.txt``

 * Start the main.py

Detailed information for each step can be found in `sphinx_doc.rst`_.


If you have any question please contact Nam Bach <thanh_nam.bach@student.reutlingen-university.de>.


.. _`venvdoc`: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
.. _`sphinx_doc.rst`: https://ttrp.readthedocs.io/en/latest/rst/installation.html
.. _Sphinx: http://sphinx-doc.org/
