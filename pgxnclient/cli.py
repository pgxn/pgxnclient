"""
pgxnclient -- command line entry point
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import sys

from pgxnclient.commands import get_option_parser, run_commands

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = get_option_parser()
    opt = parser.parse_args(argv)
    run_commands(opt, parser)

