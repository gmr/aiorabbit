"""
aiorabbit Exceptions
====================

"""
from pamqp.exceptions import *


class AIORabbitException(Exception):
    pass


class ClientNegotiationException(AIORabbitException):
    pass


class ConnectionClosedException(AIORabbitException):
    pass
