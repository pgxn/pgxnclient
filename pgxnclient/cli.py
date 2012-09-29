"""
pgxnclient -- command line entry point
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os
import sys

from pgxnclient import find_script
from pgxnclient.i18n import _
from pgxnclient.errors import PgxnException, UserAbort
from pgxnclient.commands import get_option_parser, load_commands, run_command

def main(argv=None):
    """
    The program main function.

    The function is still relatively self contained: it can be called with
    arguments and raises whatever exception, so it's the best entry point
    for whole system testing.
    """
    if argv is None:
        argv = sys.argv[1:]

    load_commands()
    parser = get_option_parser()
    opt = parser.parse_args(argv)
    run_command(opt, parser)


def script():
    """
    Execute the program as a script.

    Set up logging, invoke main() using the user-provided arguments and handle
    any exception raised.
    """
    # Setup logging
    import logging
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout)
    logger = logging.getLogger()

    # Dispatch to the command according to the script name
    script = sys.argv[0]
    args = sys.argv[1:]
    if os.path.basename(script).startswith('pgxn-'):
        args.insert(0, os.path.basename(script)[5:])
        # for help print
        sys.argv[0] = os.path.join(os.path.dirname(script), 'pgxn')

    # Execute the script
    try:
        main(args)

    # Different ways to fail
    except UserAbort, e:
        # The user replied "no" to some question
        logger.info("%s", e)
        sys.exit(1)

    except PgxnException, e:
        # An regular error from the program
        logger.error("%s", e)
        sys.exit(1)

    except SystemExit, e:
        # Usually the arg parser bailing out.
        pass

    except Exception, e:
        logger.error(_("unexpected error: %s - %s"),
            e.__class__.__name__, e, exc_info=True)
        sys.exit(1)

    except BaseException, e:
        # ctrl-c
        sys.exit(1)



def command_dispatch(argv=None):
    """
    Entry point for a script to dispatch commands to external scripts.

    Upon invocation of a command ``pgxn cmd --arg``, locate pgxn-cmd and
    execute it with --arg arguments.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Assume the first arg after the option is the command to run
    for icmd, cmd in enumerate(argv):
        if not cmd.startswith('-'):
            argv = [_get_exec(cmd)] + argv[:icmd] + argv[icmd+1:]
            break
    else:
        # No command specified: dispatch to the pgxnclient script
        # to print basic help, main command etc.
        argv = ([os.path.join(os.path.dirname(sys.argv[0]), 'pgxnclient')]
            + argv)

    if not os.access(argv[0], os.X_OK):
        # This is our friend setuptools' job: the script have lost the
        # executable flag. We assume the script is a Python one and run it
        # through the current executable.
        argv.insert(0, sys.executable)

    os.execv(argv[0], argv)

def _get_exec(cmd):
    fn = find_script('pgxn-' + cmd)
    if not fn:
        print >>sys.stderr, \
            "pgxn: unknown command: '%s'. See 'pgxn --help'" % cmd
        sys.exit(2)

    return fn

if __name__ == '__main__':
    script()

