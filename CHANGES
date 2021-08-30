.. _changes:

PGXN Client changes log
-----------------------

pgxnclient 1.3.2
================

- Fixed crash on input (ticket #42)


pgxnclient 1.3.1
================

- Fixed error running ``pgxn`` with no argument (ticket #38).
- Ignore ``.psqlrc`` file in all commands (ticket #39).
- Fixed PostgreSQL version number parsing after v10 (ticket #40).
- Added test files to the sdist package (ticket #36).
- ``tests`` directory not included in the installed package (ticket #37).


pgxnclient 1.3
==============

- Use https by default to access the PGXN API.
- Dropped support for Python < 2.7 and Python 3 < 3.4.
- Logging information emitted on stderr instead of stdout.
- Exit with nonzero return code after command line parsing errors (ticket #23).
- Don't fail if some directories in the ``PATH`` are not readable (ticket #24).
- Don't file emitting non-ascii chars with stdout redirected (ticket #26).
- Fixed parsing of server version numbers with PostgreSQL beta versions
  (ticket #29).
- Use six to make the codebase portable between Python 2 and 3.


pgxnclient 1.2.1
================

- Fixed traceback on error when a dir doesn't contain META.json (ticket #19).
- Handle version numbers both with and without hyphen (ticket #22).


pgxnclient 1.2
==============

- Packages can be downloaded, installed, loaded specifying an URL
  (ticket #15).
- Added support for ``.tar`` files (ticket #17).
- Use ``gmake`` in favour of ``make`` for platforms where the two are
  distinct, such as BSD (ticket #14).
- Added ``--make`` option to select the make executable (ticket #16).


pgxnclient 1.1
==============

- Dropped support for Python 2.4.
- ``sudo`` is not invoked automatically: the ``--sudo`` option must be
  specified if the user has not permission to write into PostgreSQL's libdir
  (ticket #13). The ``--sudo`` option can also be invoked without argument.
- Make sure the same ``pg_config`` is used both by the current user and by
  sudo.


pgxnclient 1.0.3
================

- Can deal with extensions whose ``Makefile`` is created by ``configure``
  and with makefile not in the package root. Patch provided by Hitoshi
  Harada (ticket #12).


pgxnclient 1.0.2
================

- Correctly handle PostgreSQL identifiers to be quoted (ticket #10).
- Don't crash with a traceback if some external command is not found
  (ticket #11).


pgxnclient 1.0.1
================

- Fixed simplejson dependency on Python 2.6 (ticket #8).
- Added ``pgxn help CMD`` as synonim for ``pgxn CMD --help`` (ticket #7).
- Fixed a few compatibility problems with Python 3.


pgxnclient 1.0
==============

- Extensions to load/unload from a distribution can be specified on the
  command line.
- ``pgxn help --libexec`` returns a single directory, possibly independent
  from the client version.


pgxnclient 0.3
==============

- ``pgxn`` script converted into a generic dispatcher in order to allow
  additional commands to be implemented in external scripts and in any
  language.
- commands accept extension names too, not only specs.
- Added ``help`` command to get information about program and commands.


pgxnclient 0.2.1
================

- Lowercase search for distributions in the API (issue #3).
- Fixed handling of zip files not containing entries for the directory.
- More informative error messages when some item is not found on PGXN.


pgxnclient 0.2
==============

- Dropped ``list`` command (use ``info --versions`` instead).
- Skip extension load/unload if the provided file is not sql.


pgxnclient 0.1a4
================

- The spec can point to a local file/directory for install.
- Read the sha1 from the ``META.json`` as it may be different from the one
  in the ``dist.json``.
- Run sudo in the installation phase of the install command.


pgxn.client 0.1a3
=================

- Fixed executable mode for scripts unpacked from the zip files.
- Added ``list`` and ``info`` commands.


pgxn.client 0.1a2
=================

- Added database connection parameters for the ``check`` command.


pgxn.client 0.1a1
=================

- Fist version released on PyPI.
