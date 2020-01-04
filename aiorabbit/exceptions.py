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
