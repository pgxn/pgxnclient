"""
pgxnclient -- command line entry point
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import sys

from pgxnclient.commands import get_option_parser, load_commands, run_commands

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    load_commands()
    parser = get_option_parser()
    opt = parser.parse_args(argv)
    run_commands(opt, parser)

