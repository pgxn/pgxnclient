"""
pgxnclient -- help commands implementation
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os

from pgxnclient import get_scripts_dirs, get_public_scripts_dir
from pgxnclient.i18n import _, N_
from pgxnclient.commands import Command

class Help(Command):
    name = 'help'
    description = N_("display help and other program information")

    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        subp = super(Help, self).customize_parser(
            parser, subparsers, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--all', action="store_true",
            help = _("list all the available commands"))
        g.add_argument('--libexec', action="store_true",
            help = _("print the location of the scripts directory"))
        g.add_argument('command', metavar='CMD', nargs='?',
            help = _("the command to get help about"))

        # To print the basic help
        self._parser = parser

        return subp

    def run(self):
        if self.opts.command:
            from pgxnclient.cli import main
            main([self.opts.command, '--help'])
        elif self.opts.all:
            self.print_all_commands()
        elif self.opts.libexec:
            self.print_libexec()
        else:
            self._parser.print_help()

    def print_all_commands(self):
        cmds = self.find_all_commands()
        title = _("Available PGXN Client commands")
        print title
        print "-" * len(title)

        for cmd in cmds:
            print "  " + cmd

    def find_all_commands(self):
        rv = []
        path = os.environ.get('PATH', '').split(os.pathsep)
        path[0:0] = get_scripts_dirs()
        for p in path:
            if not os.path.isdir(p):
                continue
            for fn in os.listdir(p):
                if fn.startswith('pgxn-'):
                    rv.append(fn[5:])

        rv.sort()
        return rv

    def print_libexec(self):
        print get_public_scripts_dir()

