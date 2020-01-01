"""
Channel 0
=========

Handles all communication on Channel0

"""
import asyncio
import logging
import platform
import typing

from pamqp import commands, constants, frame, header, heartbeat
from pamqp import exceptions as pamqp_exceptions

from aiorabbit import exceptions, state, version

LOGGER = logging.getLogger(__name__)

COMMANDS = typing.Union[commands.Connection.Blocked,
                        commands.Connection.Unblocked,
                        commands.Connection.Start,
                        commands.Connection.Tune,
                        commands.Connection.OpenOk,
                        commands.Connection.Close,
                        commands.Connection.CloseOk,
                        heartbeat.Heartbeat]

FRAMES: typing.Final[set] = {
    'Connection.Blocked',
    'Connection.Unblocked',
    'Connection.Start',
    'Connection.Tune',
    'Connection.OpenOk',
    'Connection.Close',
    'Connection.CloseOk',
    'Heartbeat'
}


class Channel0(state.StateManager):

    STATE_UNINITIALIZED: typing.Final[int] = 0x00
    STATE_PROTOCOL_HEADER_SENT: typing.Final[int] = 0x01
    STATE_START_RECEIVED: typing.Final[int] = 0x02
    STATE_START_OK_SENT: typing.Final[int] = 0x03
    STATE_TUNE_RECEIVED: typing.Final[int] = 0x04
    STATE_TUNE_OK_SENT: typing.Final[int] = 0x05
    STATE_OPEN_SENT: typing.Final[int] = 0x06
    STATE_OPEN_OK_RECEIVED: typing.Final[int] = 0x07
    STATE_HEARTBEAT_RECEIVED: typing.Final[int] = 0x08
    STATE_HEARTBEAT_SENT: typing.Final[int] = 0x09
    STATE_CLOSE_RECEIVED: typing.Final[int] = 0x10
    STATE_CLOSE_SENT: typing.Final[int] = 0x11
    STATE_CLOSE_OK_SENT: typing.Final[int] = 0x12
    STATE_BLOCKED_RECEIVED: typing.Final[int] = 0x13
    STATE_UNBLOCKED_RECEIVED: typing.Final[int] = 0x14
    STATE_CLOSED: typing.Final[int] = 0x15

    STATE_MAP: typing.Final[dict] = {
        0x00: 'Uninitialized',
        0x01: 'Protocol Header Received',
        0x02: 'Start Received',
        0x03: 'StartOk Sent',
        0x04: 'Tune Received',
        0x05: 'TuneOk Sent',
        0x06: 'Open Sent',
        0x07: 'OpenOk Received',
        0x08: 'Heartbeat Received',
        0x09: 'Heartbeat Sent',
        0x10: 'Connection Close Received',
        0x11: 'Connection Close Sent',
        0x12: 'Connection CloseOk Sent',
        0x13: 'Connection Blocked Received',
        0x14: 'Connection Unblocked Received',
        0x15: 'Closed'
    }

    STATE_TRANSITIONS: typing.Final[dict] = {
        STATE_UNINITIALIZED: {
            STATE_PROTOCOL_HEADER_SENT},
        STATE_PROTOCOL_HEADER_SENT: {
            STATE_START_RECEIVED,
            STATE_CLOSED},
        STATE_START_RECEIVED: {
            STATE_START_OK_SENT,
            STATE_CLOSED},
        STATE_START_OK_SENT: {
            STATE_TUNE_RECEIVED,
            STATE_CLOSED},
        STATE_TUNE_RECEIVED: {
            STATE_TUNE_OK_SENT},
        STATE_TUNE_OK_SENT: {
            STATE_OPEN_SENT},
        STATE_OPEN_SENT: {
            STATE_OPEN_OK_RECEIVED},
        STATE_OPEN_OK_RECEIVED: {
            STATE_BLOCKED_RECEIVED,
            STATE_HEARTBEAT_RECEIVED,
            STATE_CLOSE_RECEIVED,
            STATE_CLOSE_SENT,
            STATE_CLOSED},
        STATE_CLOSE_RECEIVED: {
            STATE_CLOSE_OK_SENT,
            STATE_CLOSED},
        STATE_CLOSE_SENT: {
            STATE_CLOSED},
        STATE_CLOSE_OK_SENT: {
            STATE_CLOSED},
        STATE_BLOCKED_RECEIVED: {
            STATE_UNBLOCKED_RECEIVED,
            STATE_CLOSE_RECEIVED,
            STATE_HEARTBEAT_RECEIVED,
            STATE_CLOSED},
        STATE_UNBLOCKED_RECEIVED: {
            STATE_CLOSE_RECEIVED,
            STATE_HEARTBEAT_RECEIVED,
            STATE_CLOSED},
        STATE_HEARTBEAT_RECEIVED: {
            STATE_HEARTBEAT_SENT,
            STATE_BLOCKED_RECEIVED,
            STATE_UNBLOCKED_RECEIVED,
            STATE_CLOSE_RECEIVED,
            STATE_CLOSED},
        STATE_HEARTBEAT_SENT: {
            STATE_HEARTBEAT_RECEIVED,
            STATE_BLOCKED_RECEIVED,
            STATE_UNBLOCKED_RECEIVED,
            STATE_CLOSE_RECEIVED,
            STATE_CLOSE_SENT,
            STATE_CLOSED},
        STATE_CLOSED: {
            STATE_PROTOCOL_HEADER_SENT}
    }

    def __init__(self,
                 blocked: asyncio.Event,
                 username: str,
                 password: str,
                 virtual_host: str,
                 heartbeat_interval: typing.Optional[int],
                 locale: str,
                 loop: asyncio.AbstractEventLoop,
                 max_channels: int,
                 product: str):
        super().__init__(loop)
        self.blocked = blocked
        self.locale = locale
        self.password = password
        self.product = product
        self.properties: dict = {}
        self.transport: typing.Optional[asyncio.Transport] = None
        self.username = username
        self.virtual_host = virtual_host
        self.heartbeat_interval = heartbeat_interval
        self.max_frame_size = constants.FRAME_MAX_SIZE
        self.max_channels = max_channels

    def process(self, value: COMMANDS) -> None:
        LOGGER.debug('Processing %r', value)
        if isinstance(value, commands.Connection.Start):
            self._set_state(self.STATE_START_RECEIVED)
            self._process_start(value)
        elif isinstance(value, commands.Connection.Tune):
            self._set_state(self.STATE_TUNE_RECEIVED)
            self._process_tune(value)
        elif isinstance(value, commands.Connection.OpenOk):
            self._set_state(self.STATE_OPEN_OK_RECEIVED)
        elif isinstance(value, commands.Connection.Blocked):
            self._set_state(self.STATE_BLOCKED_RECEIVED)
            self.blocked.set()
        elif isinstance(value, commands.Connection.Unblocked):
            self._set_state(self.STATE_UNBLOCKED_RECEIVED)
            self.blocked.clear()
        elif isinstance(value, commands.Connection.Close):
            self._set_state(self.STATE_CLOSE_RECEIVED)
            self._process_close(value)
        elif isinstance(value, commands.Connection.CloseOk):
            self._set_state(self.STATE_CLOSED)
        elif isinstance(value, heartbeat.Heartbeat):
            self._set_state(self.STATE_HEARTBEAT_RECEIVED)
            self.transport.write(frame.marshal(heartbeat.Heartbeat(), 0))
            self._set_state(self.STATE_HEARTBEAT_SENT)
        else:
            self._exception = exceptions.AIORabbitException(
                'Unsupported Frame Passed to Channel0')
        if self._exception:
            raise self._exception

    async def open(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.transport.write(frame.marshal(header.ProtocolHeader(), 0))
        self._set_state(self.STATE_PROTOCOL_HEADER_SENT)
        await self._wait_on_state(
            self.STATE_OPEN_OK_RECEIVED, self.STATE_CLOSED)

    async def close(self, code=200):
        self.transport.write(frame.marshal(
            commands.Connection.Close(code, 'Client Requested', 0, 0), 0))
        self._set_state(self.STATE_CLOSE_SENT)
        await self._wait_on_state(self.STATE_CLOSED)

    @property
    def is_closed(self):
        return self._state == self.STATE_CLOSED

    @staticmethod
    def _negotiate(client: int, server: int) -> int:
        """Return the negotiated value between what the client has requested
        and the server has requested for how the two will communicate.

        """
        return min(client, server) or (client or server)

    def _process_close(self, value: commands.Connection.Close) -> None:
        LOGGER.warning('RabbitMQ closed the connection (%s): %s',
                       value.reply_code, value.reply_text)
        self.transport.write(frame.marshal(commands.Connection.CloseOk(), 0))
        if value.reply_code < 300:
            self._set_state(self.STATE_CLOSE_OK_SENT)
        elif value.reply_code in pamqp_exceptions.CLASS_MAPPING:
            self._set_state(
                self.STATE_CLOSE_OK_SENT,
                pamqp_exceptions.CLASS_MAPPING[value.reply_code](
                    value.reply_text))
        else:
            self._set_state(
                self.STATE_CLOSE_OK_SENT,
                exceptions.ConnectionClosedException(
                    value.reply_code, value.reply_text))

    def _process_start(self, value: commands.Connection.Start) -> None:
        if (value.version_major,
            value.version_minor) != (constants.VERSION[0],
                                     constants.VERSION[1]):
            LOGGER.warning('AMQP version error (received %i.%i, expected %r)',
                           value.version_major, value.version_minor,
                           constants.VERSION)
            self.transport.close()
            self._set_state(
                self.STATE_CLOSED, exceptions.ClientNegotiationException())
            return

        self.properties = dict(value.server_properties)
        for key in self.properties:
            if key == 'capabilities':
                for capability in self.properties[key]:
                    LOGGER.debug('Server supports %s: %r',
                                 capability, self.properties[key][capability])
            else:
                LOGGER.debug('Server %s: %r', key, self.properties[key])
        self.transport.write(frame.marshal(
            commands.Connection.StartOk(
                client_properties={
                    'product': self.product,
                    'platform': 'Python {}'.format(platform.python_version()),
                    'capabilities': {'authentication_failure_close': True,
                                     'basic.nack': True,
                                     'connection.blocked': True,
                                     'consumer_cancel_notify': True,
                                     'consumer_priorities': True,
                                     'direct_reply_to': True,
                                     'per_consumer_qos': True,
                                     'publisher_confirms': True},
                    'information': 'See https://aiorabbit.readthedocs.io',
                    'version': version},
                response='\0{}\0{}'.format(self.username, self.password),
                locale=self.locale), 0))
        self._set_state(self.STATE_START_OK_SENT)

    def _process_tune(self, value: commands.Connection.Tune) -> None:
        self.max_channels = self._negotiate(
            self.max_channels, value.channel_max)
        self.max_frame_size = self._negotiate(
            self.max_frame_size, value.frame_max)
        if self.heartbeat_interval is None:
            self.heartbeat_interval = value.heartbeat
        elif not self.heartbeat_interval and not value.heartbeat:
            self.heartbeat_interval = 0
        self.transport.write(frame.marshal(
            commands.Connection.TuneOk(
                self.max_channels, self.max_frame_size,
                self.heartbeat_interval), 0))
        self._set_state(self.STATE_TUNE_OK_SENT)
        self.transport.write(
            frame.marshal(commands.Connection.Open(self.virtual_host), 0))
        self._set_state(self.STATE_OPEN_SENT)
