# coding: utf-8


class AIORabbitException(Exception):
    """Exception that is the base class of all other error exceptions.
    You can use this to catch all errors with one single except statement.
    Warnings are not considered errors and thus not use this class as base.
    It is a subclass of the :exc:`Exception`.

    """


class ClientNegotiationException(AIORabbitException):
    """The client failed to connect to RabbitMQ due to a negotiation error."""


class ConnectionClosedException(AIORabbitException):
    """The remote server closed the connection or the connection was severed
    due to a networking error.

    """


class StateTransitionError(AIORabbitException):
    """The client implements a strict state machine for what is currently
    happening in the communication with RabbitMQ.

    If this exception is raised, one or more of the following is true:

    - An unexpected behavior was seen from the server
    - The client was used in an unexpect way
    - There is a bug in aiorabbit

    If you see this exception, please `create an issue
    <https://github.com/gmr/aiorabbit/issues/new>`_ in the GitHub repository
    with a full traceback and `DEBUG` level logs.

    """


class NotSupportedError(AIORabbitException):
    """Your application attempted to use a feature not supported by the
    RabbitMQ server.

    """


class InvalidRequestError(AIORabbitException):
    """The request violates the AMQ specification, usually by providing a
    value that does not validate according to the spec.

    """


class ExchangeNotFoundError(AIORabbitException):
    """A command was sent to the server referencing an exchange that does
    not exist.

    """


class CommandInvalidError(AIORabbitException):
    """The RabbitMQ server responded to a command indicating there was a
    problem with how it was used.

    """
