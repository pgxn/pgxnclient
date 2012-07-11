"""
pgxnclient -- package exceptions

These exceptions can be used to signal expected problems and to exit in a
controlled way from the program.

"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

class PgxnException(Exception):
    """Base class for the exceptions known in the pgxn package."""

class PgxnClientException(PgxnException):
    """Base class for the exceptions raised by the pgxnclient package."""

class UserAbort(PgxnClientException):
    """The user requested to stop the operation."""

class BadSpecError(PgxnClientException):
    """A bad package specification."""

class ProcessError(PgxnClientException):
    """An error raised calling an external program."""

class InsufficientPrivileges(PgxnClientException):
    """Operation will fail because the user is too lame."""

class NotFound(PgxnException):
    """Something requested by the user not found on PGXN"""

class NetworkError(PgxnClientException):
    """An error from the other side of the wire."""

class BadChecksum(PgxnClientException):
    """A downloaded file is not what expected."""

class ResourceNotFound(NetworkError):
    """Resource not found on the server."""

class BadRequestError(Exception):
    """Bad request from our side.

    This exception is a basic one because it should be rased upon an error
    on our side.
    """
