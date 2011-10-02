.. _extending:

Extending PGXN client
=====================

PGXN Client can be easily extended, either adding new builtin commands, to
be included in the `!pgxnclient` package, or writing new scripts in any
language you want.

In order to add new builtin commands, add a Python module into the
``pgxnclient/commands`` containing your command or a set of logically-related
commands. The commands are implemented by subclassing the `!Command` class.
Your commands will benefit of all the infrastructure available for the other
commands. For up-to-date informations take a look at the implementation of
builtin simple commands, such as the ones in ``info.py``.

If you are not into Python and want to add commands written in other
languages, you can provide a link (either soft or hard) to your command under
one of the ``libexec`` directories.  The exact location of the directories
depend on the client installation: distribution packagers may decide to move
them according to their own policies.  In order to know the current location
of the directories use the command ``pgxn help --libexec``. Links are also
looked for in the :envvar:`PATH` directories.

In order to implement the command :samp:`pgxn {foo}`, the link should be named
:samp:`pgxn-{foo}`. The :program:`pgxn` script will dispatch the command and
all the options to your script. Note that you can package many commands into
the same script by looking at ``argv[0]`` to know the name of the link through
which your script has been invoked.

