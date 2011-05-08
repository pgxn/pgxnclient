Program usage
=============

The program entry point is the script called :program:`pgxn`.

Usage:

.. parsed-literal::
    :class: pgxn

    pgxn [--help] [--version] [--mirror *URL*] [--verbose] [--yes]
         *COMMAND* ...

The script offers several commands, whose list can be obtained using ``pgxn
--help``. The options available for each subcommand can be obtained using
:samp:`pgxn {COMMAND} --help`.

The main commands you may be interested in are `install`_ (to download, build
and install a distribution extensions into the system) and `load`_ (to load an
installed extension into a database). Commands to perform reverse operations
are `uninstall`_ and `unload`_. Use `download`_ to get a package from a mirror
without installing it.

There are also informative commands: `search <#pgxn-search>`_ is used to
search in the repository, `info`_ to get informations about a distribution.
`mirror`_ can be used to get a list of mirrors.

The program can accept a few basic options, to be listed before the command:

:samp:`--mirror {URL}`
    Select a mirror to interact with. If not specified default to
    http://api.pgxn.org/.

``--verbose``
    Print more informations during the process.

``--yes``
    Assume affirmative answer to all questions. Useful for unattended scripts.


Package specification
---------------------

Many commands such as install_ require a *package specification* to operate.
In its simple form the specification is just the name of a distribution:
``pgxn install foo`` means "install the most recent stable release of the
package ``foo``".

The specification allows specifying an operator and a version number, so that
``pgxn install 'foo<2.0'`` will install the most recent stable release of the
package before the release 2.0. The version numbers are ordered according to
the `Semantic Versioning specification <http://semver.org/>`__. Supported
operators are ``=``, ``==`` (alias for ``=``), ``<``, ``<=``, ``>``, ``>=``.
Note that you probably need to quote the string as in the example to avoid
invoking any shell redirection command.

Whenever a command takes a specification in input, it also accepts options
``--stable``, ``--testing`` and ``--unstable`` to specify the minimum release
status accepted. The default is "stable".

A few commands also allow specifying a local ``.zip`` package or a local
directory containing a distribution: in this case the specification should
contain at least a path separator to disambiguate it from a distribution name,
for instance ``pgxn install ./foo.zip``.


.. _install:

``pgxn install``
----------------

Download, build and install a distribution on the local system.

Usage:

.. parsed-literal::
    :class: pgxn-install

    pgxn install [--help] [--stable | --testing | --unstable]
                 [--pg_config *PATH*] [--sudo *PROG* | --nosudo]
                 *SPEC*

The program takes a `package specification`_ identifying the distribution to
work with.  The download phase is skipped if the distribution specification
refers to a local directory or package.

Note that the built extension is not loaded in any database: use the command
`load`_ for this purpose.

The command will run the ``./configure`` script if available in the package,
then will perform ``make all`` and ``make install``. It is assumed that the
``Makefile`` provided by the distribution uses PGXS_ to build the extension,
but this is not enforced: you may provide any Makefile as long as the expected
commands are implemented.

.. _PGXS: http://www.postgresql.org/docs/9.1/static/extend-pgxs.html

The install phase usually requires root privileges in order to install a build
library and other files in the PostgreSQL directories: by default
:program:`sudo` will be invoked for the purpose. An alternative program can be
specified with the option :samp:`--sudo {PROG}`; ``--nosudo`` can be used to
avoid running any program.

If there are many PostgreSQL installations on the system, the extension will
be built and installed against the instance whose :program:`pg_config` is
first found on the :envvar:`PATH`. A different instance can be specified using
the option :samp:`--pg_config {PATH}`.


.. _check:

``pgxn check``
--------------

Run a distribution's unit test.

Usage:

.. parsed-literal::
    :class: pgxn-check

    pgxn check [--help] [--stable | --testing | --unstable]
               [--pg_config *PATH*] [-d *DBNAME*] [-h *HOST*] [-p *PORT*] [-U *NAME*]
               *SPEC*

The command takes a `package specification`_ identifying the distribution to
work with, which can also be a local file or directory. The distribution is
unpacked if required and the ``installcheck`` make target is run.

.. note::
    The command doesn't run ``make all`` before ``installcheck``: if any file
    required for testing is to be built, it should be listed as
    ``installcheck`` prerequisite in the ``Makefile``, for instance:

    .. code-block:: make

        myext.sql: myext.sql.in
            some_command

        installcheck: myext.sql

The script exits with non-zero value in case of test failed. In this case,
if files ``regression.diff`` and ``regression.out`` are produced (as
:program:`pg_regress` does), these files are copied to the local directory
where the script is run.

The database connection options are similar to the ones in load_, with the
difference that the variable :envvar:`PGDATABASE` doesn't influence the
database name.

.. warning::
    At the time of writing, :program:`pg_regress` on Debian and derivatives is
    affected by `bug #554166`__ which makes *HOST* selection impossible.

   .. __: http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=554166


.. _uninstall:

``pgxn uninstall``
------------------

Remove a distribution from the system.

Usage:

.. parsed-literal::
    :class: pgxn-uninstall

    pgxn uninstall [--help] [--stable | --testing | --unstable]
                   [--pg_config *PATH*] [--sudo *PROG* | --nosudo]
                   *SPEC*

The command does the opposite of the install_ command, removing a
distribution's files from the system. It doesn't issue any command to the
databases where distribution's extensions may have been loaded: you should
first drop the extension e.g. using the unload_ command.

The distribution should match what installed via the `install`_ command.

See the install_ command for details about the command arguments.


.. _load:

``pgxn load``
-------------

Load the extensions included in a distribution into a database. The
distribution must be already installed in the system, e.g. via the `install`_
command.

Usage:

.. parsed-literal::
    :class: pgxn-load

    pgxn load [--help] [--stable | --testing | --unstable] [-d *DBNAME*]
              [-h *HOST*] [-p *PORT*] [-U *NAME*] [--pg_config *PATH*]
              *SPEC*

The distribution is specified according to the `package specification`_ and
can refer to a local directory or file. No consistency check is performed
between the packages specified in the ``install`` and ``load`` command: the
specifications should refer to compatible packages. The specified distribution
is only used to read the metadata: only installed files are actually used to
issue database commands.

The database to install into can be specified using options
``-d``/``--dbname``, ``-h``/``--host``, ``-p``/``--port``,
``-U``/``--username``. The default values for these parameters are the regular
system ones and can be also set using environment variables
:envvar:`PGDATABASE`, :envvar:`PGHOST`, :envvar:`PGPORT`, :envvar:`PGUSER`.

The command supports also a ``--pg_config`` option that can be used to specify
an alternative :program:`pg_config` to use to look for installation scripts:
you may need to specify the parameter if there are many PostgreSQL
installations on the system, and should be consistent to the one specified
in the ``install`` command.

If the specified database version is at least PostgreSQL 9.1, and if the
extension specifies a ``.control`` file, it will be loaded using the `CREATE
EXTENSION`_ command, otherwise it will be loaded as a loose set of objects.
For more informations see the `extensions documentation`__.

.. _CREATE EXTENSION: http://www.postgresql.org/docs/9.1/static/sql-createextension.html
.. __: http://www.postgresql.org/docs/9.1/static/extend-extensions.html

.. todo:: Specify a schema

The command is based on the `'provides' section`_ of the distribution's
``META.json``: if a SQL file is specified, that file will be used to load the
extension. Note that loading is only attempted if the file extension is
``.sql``: if it's not, we assume that the extension is not really a PostgreSQL
extension (it may be for instance a script). If no ``file`` is specified, a
file named :samp:`{extension}.sql` will be looked for in a few directories
under the PostgreSQL ``shared`` directory and it will be loaded after an user
confirmation.

If the distribution provides more than one extension, the extensions are
loaded in the order in which they are specified in the ``provides`` section of
the ``META.json`` file.


.. _'provides' section: http://pgxn.org/spec/#provides

.. todo:: Add options to specify what to load


.. _unload:

``pgxn unload``
---------------

Unload a distribution's extensions from a database.

Usage:

.. parsed-literal::
    :class: pgxn-unload

    pgxn unload [--help] [--stable | --testing | --unstable] [-d *DBNAME*]
                [-h *HOST*] [-p *PORT*] [-U *NAME*] [--pg_config *PATH*]
                *SPEC*

The command does the opposite of the load_ command: it drops an extension from
the specified database, either issuing a `DROP EXTENSION`_ command or running
an uninstall script eventually provided.

For every extension specified in the `'provides' section`_ of the
distribution ``META.json``, the command will look for a file called
:samp:`uninstall_{file.sql}` where :samp:`{file.sql}` is the ``file``
specified. If no file is specified, :samp:`{extension}.sql` is assumed. If
a file with extension different from ``.sql`` is specified, it is
assumed that the extension is not a PostgreSQL extension so unload is not
performed.

If the distribution specifies more than one extension, they are unloaded in
reverse order respect to the order in which they are specified in the
``META.json`` file.

.. _DROP EXTENSION: http://www.postgresql.org/docs/9.1/static/sql-dropextension.html

See the load_ command for details about the command arguments.


.. _download:

``pgxn download``
-----------------

Download a distribution from the network.

Usage:

.. parsed-literal::
    :class: pgxn-download

    pgxn download [--help] [--stable | --testing | --unstable]
                  [--target *PATH*]
                  *SPEC*

The distribution is specified according to the `package specification`_.  The
file is saved in the current directory with name usually
:samp:`{distribution}-{version}.zip`. If a file with the same name exists, a
prefix ``-1``, ``-2`` etc. is added to the name, before the extension.  A
different directory or name can be specified using the ``--target`` option.


.. _pgxn-search:

``pgxn search``
---------------

Search in the extensions available on PGXN.

Usage:

.. parsed-literal::
    :class: pgxn-search

    pgxn search [--help] [--dist | --ext | --docs] *QUERY*

The prints on ``stdout`` a list of packages and version matching
:samp:`{QUERY}`. By default the search is performed in the distributions:
alternatively the extensions (using the ``--ext`` option) or the documentation
(using the ``--docs`` option) can be searched.

Example:

.. code-block:: console

    $ pgxn search integer
    tinyint 0.1.1
    check_updates 1.0.0
    ssn 1.0.0

.. todo:: Add the context to the search output?


.. _info:

``pgxn info``
-------------

Print informations about a distribution obtained from PGXN.

Usage:

.. parsed-literal::
    :class: pgxn-info

    pgxn info [--help] [--stable | --testing | --unstable]
              [--details | --meta | --readme | --versions]
              *SPEC*

The distribution is specified according to the `package specification`_.
The command output is a list of values obtained by the distribution's
``META.json`` file, for example:

.. code-block:: console

    $ pgxn info pair
    name: pair
    abstract: A key/value pair data type
    description: This library contains a single PostgreSQL extension,
    a key/value pair data type called “pair”, along with a convenience
    function for constructing key/value pairs.
    maintainer: David E. Wheeler <david@j...y.com>
    license: postgresql
    release_status: stable
    version: 0.1.2
    date: 2011-04-20T23:47:22Z
    sha1: 9988d7adb056b11f8576db44cca30f88a08bd652
    provides: pair: 0.1.2

Alternatively the raw ``META.json`` (using the ``--meta`` option) or the
distribution README (using the ``--readme`` option) can be obtained.

Using the ``--versions`` option, the command prints a list of available
versions for the specified distribution, together with their release status.
Only distributions respecting :samp:`{SPEC}` and the eventually specified
release status options are printed, for example:

.. code-block:: console

    $ pgxn info --versions 'pair<0.1.2'
    pair 0.1.1 stable
    pair 0.1.0 stable


.. _mirror:

``pgxn mirror``
---------------

Return informations about the available mirrors.

Usage:

.. parsed-literal::
    :class: pgxn-mirror

    pgxn mirror [--help] [--detailed] [*URI*]

If no :samp:`URI` is specified, print a list of known mirror URIs. Otherwise
print details about the specified mirror. It is also possible to print details
for all the known mirrors using the ``--detailed`` option.

