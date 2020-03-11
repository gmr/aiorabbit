# coding: utf-8
import datetime
import logging
import typing

from pamqp import body, commands, header

LOGGER = logging.getLogger(__name__)
METHODS = [commands.Basic.Deliver, commands.Basic.GetOk, commands.Basic.Return]


class Message:
    """Represents a message received from RabbitMQ"""
    def __init__(self, method: METHODS) -> None:
        self.method = method
        self.header: typing.Optional[header.ContentHeader] = None
        self.body_frames: typing.List[body.ContentBody] = []

    def __bytes__(self):
        """Return the message body if the instance is accessed using
        ``bytes(Message)``

        """
        return self.body

    def __len__(self):
        """Return the length of the message body"""
        return len(self.body)

    @property
    def consumer_tag(self) -> typing.Optional[str]:
        """If the delivered, the consumer tag it was delivered to"""
        if isinstance(self.method, commands.Basic.Deliver):
            return self.method.consumer_tag

    @property
    def delivery_tag(self) -> typing.Optional[int]:
        """If the message was delivered, or retrieved via Basic.Get,
        indicates the delivery tag value.

        """
        if isinstance(self.method, (commands.Basic.Deliver,
                                    commands.Basic.GetOk)):
            return self.method.delivery_tag

    @property
    def exchange(self) -> str:
        """The exchange the message was published to"""
        return self.method.exchange

    @property
    def routing_key(self) -> str:
        """The routing key the message was published with"""
        return self.method.routing_key

    @property
    def message_count(self) -> typing.Optional[int]:
        """Return the ``message_count`` if the message was retrieved using
        ``Basic.Get``

        """
        if isinstance(self.method, commands.Basic.GetOk):
            return self.method.message_count

    @property
    def redelivered(self) -> typing.Optional[bool]:
        """If the message was delivered, or retrieved via Basic.Get,
        indicates if it was redelivered

        """
        if isinstance(self.method, (commands.Basic.Deliver,
                                    commands.Basic.GetOk)):
            return self.method.redelivered

    @property
    def reply_code(self) -> typing.Optional[int]:
        """If the message was returned, includes the status code as to why"""
        if isinstance(self.method, commands.Basic.Return):
            return self.method.reply_code

    @property
    def reply_text(self) -> typing.Optional[str]:
        """If the message was returned, includes the status text as to why"""
        if isinstance(self.method, commands.Basic.Return):
            return self.method.reply_text

    @property
    def app_id(self) -> typing.Optional[str]:
        """Return the ``app_id`` property value"""
        return self.header.properties.app_id

    @property
    def content_encoding(self) -> typing.Optional[str]:
        """Return the ``content_encoding`` property value"""
        return self.header.properties.content_encoding

    @property
    def content_type(self) -> typing.Optional[str]:
        """Return the ``content_type`` property value"""
        return self.header.properties.content_type

    @property
    def correlation_id(self) -> typing.Optional[str]:
        """Return the ``correlation_id`` property value"""
        return self.header.properties.correlation_id

    @property
    def delivery_mode(self) -> typing.Optional[int]:
        """Return the ``delivery_mode`` property value"""
        return self.header.properties.delivery_mode

    @property
    def expiration(self) -> typing.Optional[str]:
        """Return the ``expiration`` property value"""
        return self.header.properties.expiration

    @property
    def headers(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Return the ``headerss`` property value"""
        return self.header.properties.headers

    @property
    def message_id(self) -> typing.Optional[str]:
        """Return the ``message_id`` property value"""
        return self.header.properties.message_id

    @property
    def message_type(self) -> typing.Optional[str]:
        """Return the ``message_type`` property value"""
        return self.header.properties.message_type

    @property
    def priority(self) -> typing.Optional[int]:
        """Return the ``priority`` property value"""
        return self.header.properties.priority

    @property
    def reply_to(self) -> typing.Optional[str]:
        """Return the ``reply_to`` property value"""
        return self.header.properties.reply_to

    @property
    def timestamp(self) -> typing.Optional[datetime.datetime]:
        """Return the ``timestamp`` property value"""
        return self.header.properties.timestamp

    @property
    def user_id(self) -> typing.Optional[str]:
        """Return the ``user_id`` property value"""
        return self.header.properties.user_id

    @property
    def body(self) -> bytes:
        """The message body"""
        return b''.join([b.value for b in self.body_frames])

    @property
    def complete(self):
        length = len(self)
        LOGGER.debug('Body size: %r, expect %r', length, self.header.body_size)
        return length == self.header.body_size
