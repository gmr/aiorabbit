# coding: utf-8
import datetime
import typing

from pamqp import body, commands, header

METHODS = typing.Union[commands.Basic.Deliver,
                       commands.Basic.GetOk,
                       commands.Basic.Return]


class Message:
    """Represents a message received from RabbitMQ

    :param method: **For internal use only**

    """
    def __init__(self, method: METHODS) -> None:
        self.method = method
        self.header: typing.Optional[header.ContentHeader] = None
        self.body_frames: typing.List[body.ContentBody] = []

    def __bytes__(self) -> bytes:
        """Return the message body if the instance is accessed using
        ``bytes(Message)``

        """
        return self.body

    def __len__(self) -> int:
        """Return the length of the message body"""
        return len(self.body)

    @property
    def consumer_tag(self) -> typing.Optional[str]:
        """If the delivered via ``Basic.Deliver``, this provides the
        consumer tag it was delivered to.

        """
        if isinstance(self.method, commands.Basic.Deliver):
            return self.method.consumer_tag

    @property
    def delivery_tag(self) -> typing.Optional[int]:
        """If the message was delivered via ``Basic.Deliver``, or retrieved via
        ``Basic.Get``, this will indicate the delivery tag value, which
        is used when acknowledging, negative-acknowledging, or rejecting the
        message.

        """
        if isinstance(self.method, (commands.Basic.Deliver,
                                    commands.Basic.GetOk)):
            return self.method.delivery_tag

    @property
    def exchange(self) -> str:
        """Provides the exchange the message was published to"""
        return self.method.exchange

    @property
    def routing_key(self) -> str:
        """Provides the routing key the message was published with"""
        return self.method.routing_key

    @property
    def message_count(self) -> typing.Optional[int]:
        """Provides the ``message_count`` if the message was retrieved using
        ``Basic.Get``

        """
        if isinstance(self.method, commands.Basic.GetOk):
            return self.method.message_count

    @property
    def redelivered(self) -> typing.Optional[bool]:
        """Indicates if the message was redelivered.

        Will return ``None`` if the message was returned via ``Basic.Return``.

        """
        if isinstance(self.method, (commands.Basic.Deliver,
                                    commands.Basic.GetOk)):
            return self.method.redelivered

    @property
    def reply_code(self) -> typing.Optional[int]:
        """If the message was returned via ``Basic.Return``, indicates the
        the error code from RabbitMQ.

        """
        if isinstance(self.method, commands.Basic.Return):
            return self.method.reply_code

    @property
    def reply_text(self) -> typing.Optional[str]:
        """If the message was returned via ``Basic.Return``, indicates the
        reason why.

        """
        if isinstance(self.method, commands.Basic.Return):
            return self.method.reply_text

    @property
    def app_id(self) -> typing.Optional[str]:
        """Provides the ``app_id`` property value if it is set."""
        return self.header.properties.app_id

    @property
    def content_encoding(self) -> typing.Optional[str]:
        """Provides the ``content_encoding`` property value if it is set."""
        return self.header.properties.content_encoding

    @property
    def content_type(self) -> typing.Optional[str]:
        """Provides the ``content_type`` property value if it is set."""
        return self.header.properties.content_type

    @property
    def correlation_id(self) -> typing.Optional[str]:
        """Provides the ``correlation_id`` property value if it is set."""
        return self.header.properties.correlation_id

    @property
    def delivery_mode(self) -> typing.Optional[int]:
        """Provides the ``delivery_mode`` property value if it is set."""
        return self.header.properties.delivery_mode

    @property
    def expiration(self) -> typing.Optional[str]:
        """Provides the ``expiration`` property value if it is set."""
        return self.header.properties.expiration

    @property
    def headers(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Provides the ``headers`` property value if it is set."""
        return self.header.properties.headers

    @property
    def message_id(self) -> typing.Optional[str]:
        """Provides the ``message_id`` property value if it is set."""
        return self.header.properties.message_id

    @property
    def message_type(self) -> typing.Optional[str]:
        """Provides the ``message_type`` property value if it is set."""
        return self.header.properties.message_type

    @property
    def priority(self) -> typing.Optional[int]:
        """Provides the ``priority`` property value if it is set."""
        return self.header.properties.priority

    @property
    def reply_to(self) -> typing.Optional[str]:
        """Provides the ``reply_to`` property value if it is set."""
        return self.header.properties.reply_to

    @property
    def timestamp(self) -> typing.Optional[datetime.datetime]:
        """Provides the ``timestamp`` property value if it is set."""
        return self.header.properties.timestamp

    @property
    def user_id(self) -> typing.Optional[str]:
        """Provides the ``user_id`` property value if it is set."""
        return self.header.properties.user_id

    @property
    def body(self) -> bytes:
        """Provides the message body"""
        return b''.join([b.value for b in self.body_frames])

    @property
    def is_complete(self):
        #  Used when receiving frames from RabbitMQ
        return len(self) == self.header.body_size
