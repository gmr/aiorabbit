"""
aiorabbit Exceptions
====================

"""


class AIORabbitException(Exception):
    pass


class ClientNegotiationException(AIORabbitException):
    pass


class ConnectionClosedException(AIORabbitException):
    pass


class StateTransitionError(AIORabbitException):
    pass


class NotSupportedError(AIORabbitException):
    pass


class InvalidRequestError(AIORabbitException):
    """The request violates the AMQ specification"""
    pass


class ExchangeNotFoundError(AIORabbitException):
    pass


class CommandInvalidError(AIORabbitException):
    pass
