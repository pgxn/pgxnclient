Installation
============

Prerequisites
-------------

The program is implemented in Python. The current version can run using Python
2.7 and 3.4 onwards.

PostgreSQL client-side development tools are required to build and install
extensions.


Installation from the Python Package Index
------------------------------------------

The PGXN client is `hosted on PyPI`__, therefore the easiest way to install
the program is through a Python installation tool such as pip_. For example a
system-wide installation can be obtained with::

    $ sudo pip install pgxnclient

To upgrade from a previous version to the most recent available you may run
instead::

    $ sudo pip install --upgrade pgxnclient

The documentation of the installation tool of your choice will also show how
to perform a local installation.

.. __: https://pypi.org/project/pgxnclient/
.. _pip: https://pip.pypa.io/en/latest/


Installation from source
------------------------

The program can also be installed from the source, either from a `source
package`__ or from the `source repository`__: in this case you can install the
program using::

    $ python setup.py install

.. __: https://pypi.org/project/pgxnclient/
.. __: https://github.com/pgxn/pgxnclient


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
    pgxnclient 1.3.0   # just an example

.. __: https://pypi.org/project/pgxnclient/
.. __: https://github.com/pgxn/pgxnclient
