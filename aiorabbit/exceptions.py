# coding: utf-8


class AIORabbitException(Exception):
    """Exception that is the base class of all other error exceptions.
    You can use this to catch all errors with one single except statement.
    Warnings are not considered errors and thus not use this class as base.
    It is a subclass of the :exc:`Exception`.

    """


class SoftError(AIORabbitException):
    """Base exception for all  soft errors."""


class HardError(AIORabbitException):
    """Base exception for all  hard errors."""


class ContentTooLarge(SoftError):
    """The client attempted to transfer content larger than the server could
    accept at the present time. The client may retry at a later time.

    """
    name = 'CONTENT-TOO-LARGE'
    value = 311


class NoConsumers(SoftError):
    """When the exchange cannot deliver to a consumer when the ``immediate``
    flag is set. As a result of pending data on the queue or the absence of any
    consumers of the queue.

    """
    name = 'NO-CONSUMERS'
    value = 313


class AccessRefused(SoftError):
    """The client attempted to work with a server entity to which it has no
    access due to security settings.

    """
    name = 'ACCESS-REFUSED'
    value = 403


class NotFound(SoftError):
    """The client attempted to work with a server entity that does not exist"""
    name = 'NOT-FOUND'
    value = 404


class ResourceLocked(SoftError):
    """The client attempted to work with a server entity to which it has no
    access because another client is working with it.

    """
    name = 'RESOURCE-LOCKED'
    value = 405


class PreconditionFailed(SoftError):
    """The client requested a method that was not allowed because some
    precondition failed.

    """
    name = 'PRECONDITION-FAILED'
    value = 406


class ConnectionForced(HardError):
    """An operator intervened to close the connection for some reason. The
    client may retry at some later date.

    """
    name = 'CONNECTION-FORCED'
    value = 320


class InvalidPath(HardError):
    """The client tried to work with an unknown virtual host"""
    name = 'INVALID-PATH'
    value = 402


class FrameError(HardError):
    """The sender sent a malformed frame that the recipient could not decode.
    This strongly implies a programming error in the sending peer.

    """
    name = 'FRAME-ERROR'
    value = 501


class SyntaxError(HardError):
    """The sender sent a frame that contained illegal values for one or more
    fields. This strongly implies a programming error in the sending peer.

    """
    name = 'SYNTAX-ERROR'
    value = 502


class CommandInvalid(HardError):
    """The client sent an invalid sequence of frames, attempting to perform an
    operation that was considered invalid by the server. This usually implies
    a programming error in the client.

    """
    name = 'COMMAND-INVALID'
    value = 503


class ChannelError(HardError):
    """The client attempted to work with a channel that had not been correctly
    opened. This most likely indicates a fault in the client layer.

    """
    name = 'CHANNEL-ERROR'
    value = 504


class UnexpectedFrame(HardError):
    """The peer sent a frame that was not expected, usually in the context of
    a content header and body.  This strongly indicates a fault in the peer's
    content processing.

    """
    name = 'UNEXPECTED-FRAME'
    value = 505


class ResourceError(HardError):
    """The server could not complete the method because it lacked sufficient
    resources. This may be due to the client creating too many of some type
    of entity.

    """
    name = 'RESOURCE-ERROR'
    value = 506


class NotAllowed(HardError):
    """The client tried to work with some entity in a manner that is
    prohibited by the server, due to security settings or by some other
    criteria.

    """
    name = 'NOT-ALLOWED'
    value = 530


class NotImplemented(HardError):
    """The client tried to use functionality that is not implemented in the
    server.

    """
    name = 'NOT-IMPLEMENTED'
    value = 540


class InternalError(HardError):
    """The server could not complete the method because of an internal error.
    The server may require intervention by an operator in order to resume
    normal operations.

    """
    name = 'INTERNAL-ERROR'
    value = 541


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


class InvalidRequestError(AIORabbitException):
    """The request violates the AMQ specification, usually by providing a
    value that does not validate according to the spec.

    """


class NoTransactionError(AIORabbitException):
    """Commit or Rollback Invoked without a Transaction

    :meth:`~aiorabbit.client.Client.tx_commit` or
    :meth:`~aiorabbit.client.Client.tx_rollback`
    were invoked without first invoking
    :meth:`~aiorabbit.client.Client.tx_select`.

    """


#  Error code to class mapping
CLASS_MAPPING = {
    311: ContentTooLarge,
    313: NoConsumers,
    403: AccessRefused,
    404: NotFound,
    405: ResourceLocked,
    406: PreconditionFailed,
    320: ConnectionForced,
    402: InvalidPath,
    501: FrameError,
    502: SyntaxError,
    503: CommandInvalid,
    504: ChannelError,
    505: UnexpectedFrame,
    506: ResourceError,
    530: NotAllowed,
    540: NotImplemented,
    541: InternalError
}
