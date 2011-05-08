Installation
============

Prerequisites
-------------

The program is implemented in Python. Versions from Python 2.4 onwards are
supported, including Python 3.0 and successive.

PostgreSQL client-side development tools are required to build and install
extensions.


Installation from the Python Package Index
------------------------------------------

The PGXN client is `hosted on PyPI`__, therefore the easiest way to install
the program is through a Python installation tool such as easy_install_, pip_
or `zc.buildout`_. For example a system-wide installation can be obtained
with::

    $ sudo easy_install pgxnclient

The documentation of the tools will also show how to perform a local
installation.

.. __: http://pypi.python.org/pypi/pgxnclient
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip: http://www.pip-installer.org/en/latest/
.. _zc.buildout: http://www.buildout.org/


Installation from source
------------------------

The program can be also installed from the source, either from the git
repository or from a source package: in this case you can install the program
using::

    $ python setup.py install


