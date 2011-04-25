#!/usr/bin/env python
"""
pgxn.client -- command line interface
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import sys

from pgxn.client.i18n import _
from pgxn.client.errors import PgxnException
from pgxn.client.commands import get_option_parser, run_commands

import logging
logging.basicConfig(
    format="%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger()

def main():
    parser = get_option_parser()
    opt = parser.parse_args()
    run_commands(opt, parser)

if __name__ == '__main__':
    try:
        main()

    except PgxnException, e:
        logger.error("%s", e)
        sys.exit(1)

    except Exception, e:
        logger.error(_("unexpected error: %s - %s"),
            e.__class__.__name__, e, exc_info=True)
        sys.exit(1)

    except BaseException, e:
        # ctrl-c
        sys.exit(1)

