"""
pgxnclient -- command line entry point
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import sys

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

    # Execute the script
    try:
        main()

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


