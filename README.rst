=====================================================================
                            PGXN Client
=====================================================================
A command line tool to interact with the PostgreSQL Extension Network
=====================================================================

|travis|

.. |travis| image:: https://travis-ci.org/pgxn/pgxnclient.svg?branch=master
    :target: https://travis-ci.org/pgxn/pgxnclient
    :alt: build status

The `PGXN Client <https://pgxn.github.io/pgxnclient/>`__ is a command
line tool designed to interact with the `PostgreSQL Extension Network
<https://pgxn.org/>`__ allowing searching, compiling, installing, and removing
extensions in PostgreSQL databases.

For example, to install the semver_ extension, the client can be invoked as::

    $ pgxn install semver

which would download and compile the extension for one of the PostgreSQL
servers hosted on the machine and::

    $ pgxn load -d somedb semver

which would load the extension in one of the databases of the server.

The client interacts with the PGXN web service and a ``Makefile`` provided by
the extension. The best results are achieved with makefiles using the
PostgreSQL `Extension Building Infrastructure`__; however the client tries to
degrade gracefully in presence of any package hosted on PGXN.

.. _semver: https://pgxn.org/dist/semver
.. __: https://www.postgresql.org/docs/current/extend-pgxs.html

- Documentation: https://pgxn.github.io/pgxnclient/
- Source repository: https://github.com/pgxn/pgxnclient
- Downloads: https://pypi.python.org/pypi/pgxnclient/
- Discussion group: https://groups.google.com/group/pgxn-users/

Please refer to the files in the ``docs`` directory or online__ for
instructions about the program installation and usage.


Development
-----------

You can create a local development environment with::

    virtualenv .venv
    source .venv/bin/activate
    pip install -e .[dev]

and run `pytest` to run the test suite.

.. __: https://pgxn.github.io/pgxnclient/
