"""
AsyncIO RabbitMQ Client
=======================

"""
import asyncio
import datetime
import logging
import math
import socket
import typing
from urllib import parse

from pamqp import base, body, commands, frame, header, heartbeat
from pamqp import exceptions as pamqp_exceptions
import yarl

from aiorabbit import (channel0,
                       DEFAULT_LOCALE,
                       DEFAULT_PRODUCT,
                       DEFAULT_URL,
                       exceptions,
                       protocol,
                       state)

LOGGER = logging.getLogger(__name__)


Frame = typing.Union[base.Frame,
                     body.ContentBody,
                     header.ContentHeader,
                     heartbeat.Heartbeat]

STATE_DISCONNECTED = 0x11
STATE_CONNECTING = 0x12
STATE_CONNECTED = 0x13
STATE_OPENED = 0x14
STATE_UPDATE_SECRET_SENT = 0x15
STATE_UPDATE_SECRETOK_RECEIVED = 0x16
STATE_CHANNEL_OPEN_SENT = 0x17
STATE_CHANNEL_OPENOK_RECEIVED = 0x18
STATE_CHANNEL_CLOSE_RECEIVED = 0x19
STATE_CHANNEL_CLOSE_SENT = 0x20
STATE_CHANNEL_CLOSEOK_RECEIVED = 0x21
STATE_CHANNEL_FLOW_RECEIVED = 0x22
STATE_CHANNEL_FLOWOK_SENT = 0x23
STATE_CONFIRM_SELECT_SENT = 0x24
STATE_CONFIRM_SELECTOK_RECEIVED = 0x25
STATE_EXCHANGE_BIND_SENT = 0x26
STATE_EXCHANGE_BINDOK_RECEIVED = 0x27
STATE_EXCHANGE_DECLARE_SENT = 0x28
STATE_EXCHANGE_DECLAREOK_RECEIVED = 0x29
STATE_EXCHANGE_DELETE_SENT = 0x30
STATE_EXCHANGE_DELETEOK_RECEIVED = 0x31
STATE_EXCHANGE_UNBIND_SENT = 0x32
STATE_EXCHANGE_UNBINDOK_RECEIVED = 0x33
STATE_QUEUE_BIND_SENT = 0x34
STATE_QUEUE_BINDOK_RECEIVED = 0x35
STATE_QUEUE_DECLARE_SENT = 0x36
STATE_QUEUE_DECLAREOK_RECEIVED = 0x37
STATE_QUEUE_DELETE_SENT = 0x38
STATE_QUEUE_DELETEOK_RECEIVED = 0x39
STATE_QUEUE_PURGE_SENT = 0x40
STATE_QUEUE_PURGEOK_RECEIVED = 0x41
STATE_QUEUE_UNBIND_SENT = 0x42
STATE_QUEUE_UNBINDOK_RECEIVED = 0x43
STATE_TX_SELECT_SENT = 0x44
STATE_TX_SELECTOK_RECEIVED = 0x45
STATE_TX_COMMIT_SENT = 0x46
STATE_TX_COMMITOK_RECEIVED = 0x47
STATE_TX_ROLLBACK_SENT = 0x48
STATE_TX_ROLLBACKOK_RECEIVED = 0x49
STATE_BASIC_ACK_RECEIVED = 0x50
STATE_BASIC_ACK_SENT = 0x51
STATE_BASIC_CANCEL_RECEIVED = 0x52
STATE_BASIC_CANCEL_SENT = 0x53
STATE_BASIC_CANCELOK_RECEIVED = 0x54
STATE_BASIC_CANCELOK_SENT = 0x55
STATE_BASIC_CONSUME_SENT = 0x56
STATE_BASIC_CONSUMEOK_RECEIVED = 0x57
STATE_BASIC_DELIVER_RECEIVED = 0x58
STATE_CONTENT_HEADER_RECEIVED = 0x59
STATE_CONTENT_BODY_RECEIVED = 0x60
STATE_BASIC_GET_SENT = 0x61
STATE_BASIC_GETEMPTY_RECEIVED = 0x62
STATE_BASIC_GETOK_RECEIVED = 0x63
STATE_BASIC_NACK_RECEIVED = 0x64
STATE_BASIC_NACK_SENT = 0x65
STATE_BASIC_PUBLISH_SENT = 0x66
STATE_CONTENT_HEADER_SENT = 0x67
STATE_CONTENT_BODY_SENT = 0x68
STATE_QOS_SENT = 0x69
STATE_QOSOK_RECEIVED = 0x70
STATE_RECOVER_SENT = 0x71
STATE_RECOVEROK_RECEIVED = 0x72
STATE_BASIC_REJECT_RECEIVED = 0x73
STATE_BASIC_REJECT_SENT = 0x74
STATE_BASIC_RETURN_RECEIVED = 0x75
STATE_CLOSING = 0x76
STATE_CLOSED = 0x77

_STATE_MAP = {
    state.STATE_UNINITIALIZED: 'Uninitialized',
    state.STATE_EXCEPTION: 'Exception Raised',
    STATE_DISCONNECTED: 'Disconnected',
    STATE_CONNECTING: 'Connecting',
    STATE_CONNECTED: 'Connected',
    STATE_OPENED: 'Opened',
    STATE_UPDATE_SECRET_SENT: 'Updating Secret',
    STATE_UPDATE_SECRETOK_RECEIVED: 'Secret Updated',
    STATE_CHANNEL_OPEN_SENT: 'Opening Channel',
    STATE_CHANNEL_OPENOK_RECEIVED: 'Channel Open',
    STATE_CHANNEL_CLOSE_RECEIVED: 'Server Closed Channel',
    STATE_CHANNEL_CLOSE_SENT: 'Closing Channel',
    STATE_CHANNEL_CLOSEOK_RECEIVED: 'Channel Closed',
    STATE_CHANNEL_FLOW_RECEIVED: 'Channel Flow Received',
    STATE_CHANNEL_FLOWOK_SENT: 'Channel FlowOk Sent',
    STATE_CONFIRM_SELECT_SENT: 'Enabling Publisher Confirmations',
    STATE_CONFIRM_SELECTOK_RECEIVED: 'Publisher Confirmations Enabled',
    STATE_EXCHANGE_BIND_SENT: 'Binding Exchange',
    STATE_EXCHANGE_BINDOK_RECEIVED: 'Exchange Bound',
    STATE_EXCHANGE_DECLARE_SENT: 'Declaring Exchange',
    STATE_EXCHANGE_DECLAREOK_RECEIVED: 'Exchange Declared',
    STATE_EXCHANGE_DELETE_SENT: 'Deleting Exchange',
    STATE_EXCHANGE_DELETEOK_RECEIVED: 'Exchange Deleted',
    STATE_EXCHANGE_UNBIND_SENT: 'Unbinding Exchange',
    STATE_EXCHANGE_UNBINDOK_RECEIVED: 'Exchange unbound',
    STATE_QUEUE_BIND_SENT: 'Binding Queue',
    STATE_QUEUE_BINDOK_RECEIVED: 'Queue Bound',
    STATE_QUEUE_DECLARE_SENT: 'Declaring Queue',
    STATE_QUEUE_DECLAREOK_RECEIVED: 'Queue Declared',
    STATE_QUEUE_DELETE_SENT: 'Deleting Queue',
    STATE_QUEUE_DELETEOK_RECEIVED: 'Queue Deleted',
    STATE_QUEUE_PURGE_SENT: 'Purging Queue',
    STATE_QUEUE_PURGEOK_RECEIVED: 'Queue Purged',
    STATE_QUEUE_UNBIND_SENT: 'Unbinding Queue',
    STATE_QUEUE_UNBINDOK_RECEIVED: 'Queue unbound',
    STATE_TX_SELECT_SENT: 'Starting Transaction',
    STATE_TX_SELECTOK_RECEIVED: 'Transaction started',
    STATE_TX_COMMIT_SENT: 'Committing Transaction',
    STATE_TX_COMMITOK_RECEIVED: 'Transaction committed',
    STATE_TX_ROLLBACK_SENT: 'Aborting Transaction',
    STATE_TX_ROLLBACKOK_RECEIVED: 'Transaction aborted',
    STATE_BASIC_ACK_RECEIVED: 'Received message acknowledgement',
    STATE_BASIC_ACK_SENT: 'Sent message acknowledgement',
    STATE_BASIC_CANCEL_RECEIVED: 'Server canceled consumer',
    STATE_BASIC_CANCEL_SENT: 'Cancelling Consumer',
    STATE_BASIC_CANCELOK_RECEIVED: 'Consumer cancelled',
    STATE_BASIC_CANCELOK_SENT: 'Acknowledging cancelled consumer',
    STATE_BASIC_CONSUME_SENT: 'Initiating consuming of messages',
    STATE_BASIC_CONSUMEOK_RECEIVED: 'Consuming of messages initiated',
    STATE_BASIC_DELIVER_RECEIVED: 'Server delivered message',
    STATE_CONTENT_HEADER_RECEIVED: 'Received content header',
    STATE_CONTENT_BODY_RECEIVED: 'Received content body',
    STATE_BASIC_GET_SENT: 'Requesting individual message',
    STATE_BASIC_GETEMPTY_RECEIVED: 'Message not available',
    STATE_BASIC_GETOK_RECEIVED: 'Individual message to be delivered',
    STATE_BASIC_NACK_RECEIVED: 'Server sent negative acknowledgement',
    STATE_BASIC_NACK_SENT: 'Sending negative acknowledgement',
    STATE_BASIC_PUBLISH_SENT: 'Publishing Message',
    STATE_CONTENT_HEADER_SENT: 'Message Content Header sent',
    STATE_CONTENT_BODY_SENT: 'Message Body sent',
    STATE_QOS_SENT: 'Setting QoS',
    STATE_QOSOK_RECEIVED: 'QoS set',
    STATE_RECOVER_SENT: 'Sending recover request',
    STATE_RECOVEROK_RECEIVED: 'Recover request received',
    STATE_BASIC_REJECT_RECEIVED: 'Server rejected Message',
    STATE_BASIC_REJECT_SENT: 'Sending Message rejection',
    STATE_BASIC_RETURN_RECEIVED: 'Server returned message',
    STATE_CLOSING: 'Closing',
    STATE_CLOSED: 'Closed',
}

_IDLE_STATE = [
    STATE_UPDATE_SECRET_SENT,
    STATE_CHANNEL_CLOSE_RECEIVED,
    STATE_CHANNEL_CLOSE_SENT,
    STATE_CHANNEL_FLOW_RECEIVED,
    STATE_CONFIRM_SELECT_SENT,
    STATE_EXCHANGE_BIND_SENT,
    STATE_EXCHANGE_DECLARE_SENT,
    STATE_EXCHANGE_DELETE_SENT,
    STATE_EXCHANGE_UNBIND_SENT,
    STATE_QUEUE_BIND_SENT,
    STATE_QUEUE_DECLARE_SENT,
    STATE_QUEUE_DELETE_SENT,
    STATE_QUEUE_PURGE_SENT,
    STATE_QUEUE_UNBIND_SENT,
    STATE_TX_SELECT_SENT,
    STATE_TX_COMMIT_SENT,
    STATE_TX_ROLLBACK_SENT,
    STATE_BASIC_ACK_RECEIVED,
    STATE_BASIC_CONSUME_SENT,
    STATE_BASIC_DELIVER_RECEIVED,
    STATE_BASIC_GET_SENT,
    STATE_BASIC_NACK_RECEIVED,
    STATE_BASIC_PUBLISH_SENT,
    STATE_BASIC_REJECT_RECEIVED,
    STATE_BASIC_RETURN_RECEIVED,
    STATE_QOS_SENT,
    STATE_RECOVER_SENT,
    STATE_CLOSING,
    STATE_CLOSED
]

_STATE_TRANSITIONS = {
    state.STATE_UNINITIALIZED: [STATE_DISCONNECTED],
    state.STATE_EXCEPTION: [STATE_CLOSING, STATE_CLOSED],
    STATE_DISCONNECTED: [STATE_CONNECTING],
    STATE_CONNECTING: [STATE_CONNECTED],
    STATE_CONNECTED: [STATE_OPENED],
    STATE_OPENED: [STATE_CHANNEL_OPEN_SENT],
    STATE_UPDATE_SECRET_SENT: [STATE_UPDATE_SECRETOK_RECEIVED],
    STATE_UPDATE_SECRETOK_RECEIVED: _IDLE_STATE,
    STATE_CHANNEL_OPEN_SENT: [STATE_CHANNEL_OPENOK_RECEIVED],
    STATE_CHANNEL_OPENOK_RECEIVED: _IDLE_STATE,
    STATE_CHANNEL_CLOSE_RECEIVED: [STATE_CHANNEL_OPEN_SENT],
    STATE_CHANNEL_CLOSE_SENT: [STATE_CHANNEL_CLOSEOK_RECEIVED],
    STATE_CHANNEL_CLOSEOK_RECEIVED: [STATE_CHANNEL_OPEN_SENT],
    STATE_CHANNEL_FLOW_RECEIVED: [STATE_CHANNEL_FLOWOK_SENT],
    STATE_CHANNEL_FLOWOK_SENT: _IDLE_STATE,
    STATE_CONFIRM_SELECT_SENT: [STATE_CONFIRM_SELECTOK_RECEIVED],
    STATE_CONFIRM_SELECTOK_RECEIVED: _IDLE_STATE,
    STATE_EXCHANGE_BIND_SENT: [STATE_EXCHANGE_BINDOK_RECEIVED],
    STATE_EXCHANGE_BINDOK_RECEIVED: _IDLE_STATE,
    STATE_EXCHANGE_DECLARE_SENT: [STATE_EXCHANGE_DECLAREOK_RECEIVED],
    STATE_EXCHANGE_DECLAREOK_RECEIVED: _IDLE_STATE,
    STATE_EXCHANGE_DELETE_SENT: [STATE_EXCHANGE_DELETEOK_RECEIVED],
    STATE_EXCHANGE_DELETEOK_RECEIVED: _IDLE_STATE,
    STATE_EXCHANGE_UNBIND_SENT: [STATE_EXCHANGE_UNBINDOK_RECEIVED],
    STATE_EXCHANGE_UNBINDOK_RECEIVED: _IDLE_STATE,
    STATE_QUEUE_BIND_SENT: [STATE_QUEUE_BINDOK_RECEIVED],
    STATE_QUEUE_BINDOK_RECEIVED: _IDLE_STATE,
    STATE_QUEUE_DECLARE_SENT: [STATE_QUEUE_DECLAREOK_RECEIVED],
    STATE_QUEUE_DECLAREOK_RECEIVED: _IDLE_STATE,
    STATE_QUEUE_DELETE_SENT: [STATE_QUEUE_DELETEOK_RECEIVED],
    STATE_QUEUE_DELETEOK_RECEIVED: _IDLE_STATE,
    STATE_QUEUE_PURGE_SENT: [STATE_QUEUE_PURGEOK_RECEIVED],
    STATE_QUEUE_PURGEOK_RECEIVED: _IDLE_STATE,
    STATE_QUEUE_UNBIND_SENT: [STATE_QUEUE_UNBINDOK_RECEIVED],
    STATE_QUEUE_UNBINDOK_RECEIVED: _IDLE_STATE,
    STATE_TX_SELECT_SENT: [STATE_TX_SELECTOK_RECEIVED],
    STATE_TX_SELECTOK_RECEIVED: _IDLE_STATE + [
        STATE_TX_COMMIT_SENT,
        STATE_TX_ROLLBACK_SENT
    ],
    STATE_TX_COMMIT_SENT: [STATE_TX_COMMITOK_RECEIVED],
    STATE_TX_COMMITOK_RECEIVED: _IDLE_STATE,
    STATE_TX_ROLLBACK_SENT: [STATE_TX_ROLLBACKOK_RECEIVED],
    STATE_TX_ROLLBACKOK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_ACK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_ACK_SENT: _IDLE_STATE,
    STATE_BASIC_CANCEL_RECEIVED: _IDLE_STATE,
    STATE_BASIC_CANCEL_SENT: [STATE_BASIC_CANCELOK_RECEIVED],
    STATE_BASIC_CANCELOK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_CANCELOK_SENT: _IDLE_STATE,
    STATE_BASIC_CONSUME_SENT: [STATE_BASIC_CONSUMEOK_RECEIVED],
    STATE_BASIC_CONSUMEOK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_DELIVER_RECEIVED: [STATE_CONTENT_HEADER_RECEIVED],
    STATE_CONTENT_HEADER_RECEIVED: [STATE_CONTENT_BODY_RECEIVED],
    STATE_BASIC_GET_SENT: [
        STATE_BASIC_GETEMPTY_RECEIVED,
        STATE_BASIC_GETOK_RECEIVED],
    STATE_BASIC_GETEMPTY_RECEIVED: _IDLE_STATE,
    STATE_BASIC_GETOK_RECEIVED: [STATE_CONTENT_HEADER_RECEIVED],
    STATE_BASIC_NACK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_NACK_SENT: _IDLE_STATE,
    STATE_BASIC_PUBLISH_SENT: [STATE_CONTENT_HEADER_SENT],
    STATE_CONTENT_HEADER_SENT: [STATE_CONTENT_BODY_SENT],
    STATE_CONTENT_BODY_SENT: _IDLE_STATE,
    STATE_QOS_SENT: [STATE_QOSOK_RECEIVED],
    STATE_QOSOK_RECEIVED: _IDLE_STATE,
    STATE_RECOVER_SENT: [STATE_RECOVEROK_RECEIVED],
    STATE_RECOVEROK_RECEIVED: _IDLE_STATE,
    STATE_BASIC_REJECT_RECEIVED: _IDLE_STATE,
    STATE_BASIC_REJECT_SENT: _IDLE_STATE,
    STATE_BASIC_RETURN_RECEIVED: [STATE_CONTENT_HEADER_RECEIVED],
    STATE_CLOSING: [STATE_CLOSED],
    STATE_CLOSED: [STATE_CONNECTING]
}


class Client(state.StateManager):
    """RabbitMQ Client"""

    STATE_MAP = _STATE_MAP
    STATE_TRANSITIONS = _STATE_TRANSITIONS

    def __init__(self,
                 url: str = DEFAULT_URL,
                 locale: str = DEFAULT_LOCALE,
                 product: str = DEFAULT_PRODUCT,
                 loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        LOGGER.info('Creating new client.Client')
        super().__init__(loop or asyncio.get_running_loop())
        self._blocked = asyncio.Event()
        self._channel: int = 0
        self._connected = asyncio.Event()
        self._transport: typing.Optional[asyncio.Transport] = None
        self._protocol: typing.Optional[asyncio.Protocol] = None
        self._publisher_confirms = False
        self._url = yarl.URL(url)
        self._set_state(STATE_DISCONNECTED)
        self._channel0 = channel0.Channel0(
            self._blocked, self._url.user, self._url.password,
            self._url.path[1:], self._url.query.get('heartbeat'), locale,
            self._loop, int(self._url.query.get('channel_max', '32768')),
            product)
        self._max_frame_size = float(self._channel0.max_frame_size)

    async def connect(self) -> None:
        """Connect to the RabbitMQ Server"""
        await self._connect()
        await self._open_channel()

    async def close(self) -> None:
        LOGGER.debug('Invoked Client.close()')
        if self._channel0.is_closed or not self._transport:
            LOGGER.warning('Connection is already closed')
            return
        self._set_state(STATE_CLOSING)
        await self._channel0.close()
        self._transport.close()
        await self._wait_on_state(STATE_CLOSED)
        self._reset()

    async def confirm_select(self) -> None:
        """Turn on Publisher Confirmations

        :raises: :exc:`RuntimeError`
        :raises: :exc:`aiorabbit.exceptions.NotSupportedError`

        """
        LOGGER.debug('Enabling confirm select')
        if not self.server_capabilities.get('publisher_confirms'):
            self._set_state(
                state.STATE_EXCEPTION,
                exceptions.NotSupportedError(
                    'Server does not support publisher confirmations'))
        elif self._publisher_confirms:
            self._set_state(
                state.STATE_EXCEPTION,
                RuntimeError('Publisher confirmations are already enabled'))
        else:
            self._write(commands.Confirm.Select())
            self._set_state(STATE_CONFIRM_SELECT_SENT)
        await self._wait_on_state(STATE_CONFIRM_SELECTOK_RECEIVED)
        self._publisher_confirms = True

    async def publish(self,
                      exchange: str = 'amq.direct',
                      routing_key: str = '',
                      message_body: typing.Union[bytes, str] = b'',
                      mandatory: bool = False,
                      immediate: bool = False,
                      app_id: typing.Optional[str] = None,
                      content_encoding: typing.Optional[str] = None,
                      content_type: typing.Optional[str] = None,
                      correlation_id: typing.Optional[str] = None,
                      delivery_mode: typing.Optional[int] = None,
                      expiration: typing.Optional[str] = None,
                      headers: typing.Optional[dict] = None,
                      message_id: typing.Optional[str] = None,
                      message_type: typing.Optional[str] = None,
                      priority: typing.Optional[int] = None,
                      reply_to: typing.Optional[str] = None,
                      timestamp: typing.Optional[datetime.datetime] = None,
                      user_id: typing.Optional[str] = None) \
            -> typing.Optional[bool]:
        """Publish a message to RabbitMQ

        `message_body` can either be :py:class:`str` or :py:class:`bytes`. If
        it is a :py:class:`str`, it will be encoded, using ``UTF-8`` encoding.

        If publisher confirmations are enabled (see
        :meth:`~Client.confirm_select`), will return bool indicating success
        or failure.

        :param exchange: The exchange to publish to. Default: `amq.direct`
        :param routing_key: The routing key to publish with. Default: ``
        :param message_body: The message body to publish. Default: ``
        :param mandatory: Indicate mandatory routing
        :param immediate: Request immediate delivery
        :param app_id: Creating application id
        :param content_type: MIME content type
        :param content_encoding: MIME content encoding
        :param correlation_id: Application correlation identifier
        :param delivery_mode: Non-persistent (1) or persistent (2)
        :param expiration: Message expiration specification
        :param headers: Message header field table
        :param message_id: Application message identifier
        :param message_type: Message type name
        :param priority: Message priority, 0 to 9
        :param reply_to: Address to reply to
        :param timestamp: Message timestamp
        :param user_id: Creating user id
        :raises: TypeError
        :raises: ValueError

        """
        if not isinstance(exchange, str):
            raise TypeError('exchange must be of type str')
        elif not isinstance(routing_key, str):
            raise TypeError('routing_key must be of type str')
        elif not isinstance(message_body, (bytes, str)):
            raise TypeError('message_body must be of types bytes or str')
        elif mandatory is not None and not isinstance(mandatory, bool):
            raise TypeError('mandatory must be of type bool')
        elif immediate is not None and not isinstance(immediate, bool):
            raise TypeError('immediate must be of type bool')
        elif app_id and not isinstance(app_id, str):
            raise TypeError('app_id must be of type str')
        elif content_encoding and not isinstance(content_encoding, str):
            raise TypeError('content_encoding must be of type str')
        elif content_type and not isinstance(content_type, str):
            raise TypeError('content_type must be of type str')
        elif correlation_id and not isinstance(correlation_id, str):
            raise TypeError('correlation_id must be of type str')
        elif delivery_mode and delivery_mode not in [1, 2]:
            raise ValueError('delivery_mode must be 1 or 2')
        elif expiration and not isinstance(expiration, str):
            raise TypeError('expiration must be of type str')
        elif headers and not isinstance(headers, dict):
            raise TypeError('headers must be of type dict')
        elif message_id and not isinstance(message_id, str):
            raise TypeError('message_id must be of type str')
        elif message_type and not isinstance(message_type, str):
            raise TypeError('message_type must be of type str')
        elif priority and (not isinstance(priority, int)
                           or not 0 < priority < 256):
            raise ValueError('priority must be of type int between 0 and 256')
        elif reply_to and not isinstance(reply_to, str):
            raise TypeError('reply_to must be of type str')
        elif timestamp and not isinstance(timestamp, datetime.datetime):
            raise TypeError('reply_to must be of type datetime.datetime')
        elif user_id and not isinstance(user_id, str):
            raise TypeError('user_id must be of type str')

        if isinstance(message_body, str):
            message_body = message_body.encode('utf-8')
        self._write(commands.Basic.Publish(
            exchange=exchange, routing_key=routing_key, mandatory=mandatory,
            immediate=immediate))
        self._set_state(STATE_BASIC_PUBLISH_SENT)

        body_size = len(message_body)
        self._write(header.ContentHeader(
            body_size=body_size,
            properties=commands.Basic.Properties(
                app_id=app_id,
                content_encoding=content_encoding,
                content_type=content_type,
                correlation_id=correlation_id,
                delivery_mode=delivery_mode,
                expiration=expiration,
                headers=headers,
                message_id=message_id,
                message_type=message_type,
                priority=priority,
                reply_to=reply_to,
                timestamp=timestamp,
                user_id=user_id)))
        self._set_state(STATE_CONTENT_HEADER_SENT)

        # Calculate how many body frames are needed
        pieces = int(math.ceil(body_size / self._max_frame_size))
        for offset in range(0, pieces):  # Send the message
            start = self._max_frame_size * offset
            end = start + self._max_frame_size
            if end > body_size:
                end = body_size
            self._write(body.ContentBody(message_body[start:end]))
        self._set_state(STATE_CONTENT_BODY_SENT)

        if self._publisher_confirms:
            result = await self._wait_on_state(
                STATE_CLOSED,
                STATE_CHANNEL_CLOSE_RECEIVED,
                STATE_BASIC_ACK_RECEIVED,
                STATE_BASIC_NACK_RECEIVED,
                STATE_BASIC_REJECT_RECEIVED)
            if result == STATE_BASIC_ACK_RECEIVED:
                return True
            return False

    @property
    def closed(self) -> bool:
        """Returns `True` if the connection is closed"""
        return self._state in [STATE_CLOSED,
                               state.STATE_EXCEPTION,
                               state.STATE_UNINITIALIZED] \
            and not self._transport

    @property
    def server_capabilities(self) -> dict:
        return self._channel0.properties['capabilities']

    @property
    def server_properties(self) -> dict:
        return self._channel0.properties

    async def _connect(self) -> None:
        self._set_state(STATE_CONNECTING)
        LOGGER.info('Connecting to %s://%s:%s@%s:%s/%s',
                    self._url.scheme, self._url.user,
                    ''.ljust(len(self._url.password), '*'),
                    self._url.host, self._url.port,
                    parse.quote(self._url.path[1:], ''))
        ssl = self._url.scheme == 'amqps'
        future = self._loop.create_connection(
            lambda: protocol.AMQP(
                self._on_connected,
                self._on_disconnected,
                self._on_frame,
            ), self._url.host, self._url.port,
            server_hostname=self._url.host if ssl else None,
            ssl=ssl)
        try:
            self._transport, self._protocol = await asyncio.wait_for(
                future, timeout=self._connect_timeout)
        except asyncio.TimeoutError as exc:
            self._set_state(state.STATE_EXCEPTION, exc)
            raise
        else:
            self._max_frame_size = float(self._channel0.max_frame_size)
            await self._channel0.open(self._transport)
            self._set_state(STATE_OPENED)

    async def _on_connected(self) -> None:
        self._set_state(STATE_CONNECTED)

    async def _on_disconnected(self, exc: Exception) -> None:
        LOGGER.debug('Disconnected [%r]', exc)
        self._set_state(STATE_CLOSED, exc)

    async def _on_frame(self, channel: int, value: Frame) -> None:
        if channel == 0:
            try:
                self._channel0.process(value)
            except (exceptions.AIORabbitException,
                    pamqp_exceptions.PAMQPException) as exc:
                self._set_state(state.STATE_EXCEPTION, exc)
        elif value.name == 'Channel.OpenOk':
            self._set_state(STATE_CHANNEL_OPENOK_RECEIVED)
        elif value.name == 'Confirm.SelectOk':
            self._set_state(STATE_CONFIRM_SELECTOK_RECEIVED)
        else:
            self._set_state(state.STATE_EXCEPTION,
                            RuntimeError('Main commands not supported yet'))

    async def _open_channel(self) -> None:
        self._channel += 1
        if self._channel > self._channel0.max_channels:
            self._channel = 1
        self._write(commands.Channel.Open())
        self._set_state(STATE_CHANNEL_OPEN_SENT)
        await self._wait_on_state(STATE_CHANNEL_OPENOK_RECEIVED)

    @property
    def _connect_timeout(self) -> float:
        temp = self._url.query.get('connection_timeout', '3.0')
        return socket.getdefaulttimeout() if temp is None else float(temp)

    def _reset(self) -> None:
        LOGGER.debug('Resetting internal state')
        self._blocked.clear()
        self._channel = 0
        self._connected.clear()
        self._protocol = None
        self._publisher_confirms = False
        self._transport = None

    def _write(self, value: frame.FrameTypes) -> None:
        LOGGER.debug('Writing frame %r to channel %i', value, self._channel)
        self._transport.write(frame.marshal(value, self._channel))
