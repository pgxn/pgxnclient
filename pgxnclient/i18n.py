"""
pgxnclient -- internationalization support
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


def gettext(msg):
    # TODO: real l10n
    return msg

_ = gettext

def N_(msg):
    """Designate a string to be found by gettext but not to be translated."""
    return msg
