PGXN Client's documentation
===========================

The `PGXN Client <http://pgxnclient.projects.postgresql.org/>`__ is a command
line tool designed to interact with the `PostgreSQL Extension Network
<http://pgxn.org/>`__ allowing searching, compiling, installing, and removing
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

.. _semver: http://pgxn.org/dist/semver
.. __: http://www.postgresql.org/docs/9.1/static/extend-pgxs.html

- Home page: http://pgxnclient.projects.postgresql.org/
- Downloads: http://pypi.python.org/pypi/pgxnclient/
- Discussion group: http://groups.google.com/group/pgxn-users/
- Source repository: https://github.com/dvarrazzo/pgxnclient/
- PgFoundry project: http://pgfoundry.org/projects/pgxnclient/


Contents:

.. toctree::
    :maxdepth: 2

    install
    usage
    ext

.. toctree::
    :hidden:

    changes


Indices and tables
==================

* :ref:`Changes Log <changes>`
* :ref:`search`
* :ref:`genindex`

..
    * :ref:`modindex`

..
    To do
    =====

    .. todolist::

