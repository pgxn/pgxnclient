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

To upgrade from a previous version to the most recent available you may run
instead::

    $ sudo easy_install -U pgxnclient

The documentation of the installation tool of your choice will also show how
to perform a local installation.

.. __: http://pypi.python.org/pypi/pgxnclient
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip: http://www.pip-installer.org/en/latest/
.. _zc.buildout: http://www.buildout.org/


Installation from source
------------------------

The program can also be installed from the source, either from a `source
package`__ or from the `source repository`__: in this case you can install the
program using::

    $ python setup.py install

.. __: http://pypi.python.org/pypi/pgxnclient/
.. __: https://github.com/dvarrazzo/pgxnclient/


Running from the project directory
----------------------------------

You can also run PGXN Client directly from the project directory, either
unpacked from a `source package`__, or cloned from the `source repository`__,
without performing any installation.

Just make sure that the project directory is in the :envvar:`PYTHONPATH` and
run the :program:`bin/pgxn` script::

    $ cd /path/to/pgxnclient
    $ export PYTHONPATH=`pwd`
    $ ./bin/pgxn --version
    pgxnclient 1.0.3.dev0   # just an example

.. __: http://pypi.python.org/pypi/pgxnclient/
.. __: https://github.com/dvarrazzo/pgxnclient/

