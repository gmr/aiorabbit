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

FRAMES = {
    'Connection.Blocked',
    'Connection.Unblocked',
    'Connection.Start',
    'Connection.Tune',
    'Connection.OpenOk',
    'Connection.Close',
    'Connection.CloseOk',
    'Heartbeat'
}

STATE_PROTOCOL_HEADER_SENT = 0x10
STATE_START_RECEIVED = 0x11
STATE_START_OK_SENT = 0x12
STATE_TUNE_RECEIVED = 0x13
STATE_TUNE_OK_SENT = 0x14
STATE_OPEN_SENT = 0x15
STATE_OPEN_OK_RECEIVED = 0x16
STATE_HEARTBEAT_RECEIVED = 0x17
STATE_HEARTBEAT_SENT = 0x18
STATE_CLOSE_RECEIVED = 0x19
STATE_CLOSE_SENT = 0x20
STATE_CLOSE_OK_SENT = 0x21
STATE_BLOCKED_RECEIVED = 0x22
STATE_UNBLOCKED_RECEIVED = 0x23
STATE_CLOSED = 0x24

_STATE_MAP = {
    state.STATE_UNINITIALIZED: 'Uninitialized',
    state.STATE_EXCEPTION: 'Exception Raised',
    STATE_PROTOCOL_HEADER_SENT: 'Protocol Header Sent',
    STATE_START_RECEIVED: 'Start Received',
    STATE_START_OK_SENT: 'StartOk Sent',
    STATE_TUNE_RECEIVED: 'Tune Received',
    STATE_TUNE_OK_SENT: 'TuneOk Sent',
    STATE_OPEN_SENT: 'Open Sent',
    STATE_OPEN_OK_RECEIVED: 'OpenOk Received',
    STATE_HEARTBEAT_RECEIVED: 'Heartbeat Received',
    STATE_HEARTBEAT_SENT: 'Heartbeat Sent',
    STATE_CLOSE_RECEIVED: 'Connection Close Received',
    STATE_CLOSE_SENT: 'Connection Close Sent',
    STATE_CLOSE_OK_SENT: 'Connection CloseOk Sent',
    STATE_BLOCKED_RECEIVED: 'Connection Blocked Received',
    STATE_UNBLOCKED_RECEIVED: 'Connection Unblocked Received',
    STATE_CLOSED: 'Closed'
}

_STATE_TRANSITIONS = {
    state.STATE_UNINITIALIZED: [STATE_PROTOCOL_HEADER_SENT],
    state.STATE_EXCEPTION: [],
    STATE_PROTOCOL_HEADER_SENT: [STATE_START_RECEIVED],
    STATE_START_RECEIVED: [STATE_START_OK_SENT, STATE_CLOSED],
    STATE_START_OK_SENT: [STATE_TUNE_RECEIVED],
    STATE_TUNE_RECEIVED: [STATE_TUNE_OK_SENT, STATE_CLOSED],
    STATE_TUNE_OK_SENT: [STATE_OPEN_SENT],
    STATE_OPEN_SENT: [STATE_OPEN_OK_RECEIVED],
    STATE_OPEN_OK_RECEIVED: [
        STATE_BLOCKED_RECEIVED,
        STATE_HEARTBEAT_RECEIVED,
        STATE_CLOSE_RECEIVED,
        STATE_CLOSE_SENT,
        STATE_CLOSED],
    STATE_CLOSE_RECEIVED: [STATE_CLOSE_OK_SENT],
    STATE_CLOSE_SENT: [STATE_CLOSED],
    STATE_CLOSE_OK_SENT: [STATE_CLOSED],
    STATE_BLOCKED_RECEIVED: [
        STATE_UNBLOCKED_RECEIVED,
        STATE_CLOSE_RECEIVED,
        STATE_HEARTBEAT_RECEIVED],
    STATE_UNBLOCKED_RECEIVED: [
        STATE_CLOSE_RECEIVED,
        STATE_HEARTBEAT_RECEIVED],
    STATE_HEARTBEAT_RECEIVED: [
        STATE_HEARTBEAT_SENT,
        STATE_BLOCKED_RECEIVED,
        STATE_UNBLOCKED_RECEIVED,
        STATE_CLOSE_RECEIVED],
    STATE_HEARTBEAT_SENT: [
        STATE_HEARTBEAT_RECEIVED,
        STATE_BLOCKED_RECEIVED,
        STATE_UNBLOCKED_RECEIVED,
        STATE_CLOSE_RECEIVED,
        STATE_CLOSE_SENT],
    STATE_CLOSED: [STATE_PROTOCOL_HEADER_SENT]
}


class Channel0(state.StateManager):
    """Manages the state of the connection on Channel 0"""

    STATE_MAP = _STATE_MAP
    STATE_TRANSITIONS = _STATE_TRANSITIONS

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
            self._set_state(STATE_START_RECEIVED)
            self._process_start(value)
        elif isinstance(value, commands.Connection.Tune):
            self._set_state(STATE_TUNE_RECEIVED)
            self._process_tune(value)
        elif isinstance(value, commands.Connection.OpenOk):
            self._set_state(STATE_OPEN_OK_RECEIVED)
        elif isinstance(value, commands.Connection.Blocked):
            self._set_state(STATE_BLOCKED_RECEIVED)
            self.blocked.set()
        elif isinstance(value, commands.Connection.Unblocked):
            self._set_state(STATE_UNBLOCKED_RECEIVED)
            self.blocked.clear()
        elif isinstance(value, commands.Connection.Close):
            self._set_state(STATE_CLOSE_RECEIVED)
            self._process_close(value)
        elif isinstance(value, commands.Connection.CloseOk):
            self._set_state(STATE_CLOSED)
        elif isinstance(value, heartbeat.Heartbeat):
            self._set_state(STATE_HEARTBEAT_RECEIVED)
            self.transport.write(frame.marshal(heartbeat.Heartbeat(), 0))
            self._set_state(STATE_HEARTBEAT_SENT)
        else:
            self._set_state(state.STATE_EXCEPTION,
                            exceptions.AIORabbitException(
                                'Unsupported Frame Passed to Channel0'))
        if self.exception:
            raise self.exception

    async def open(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.transport.write(frame.marshal(header.ProtocolHeader(), 0))
        self._set_state(STATE_PROTOCOL_HEADER_SENT)
        await self._wait_on_state(
            STATE_OPEN_OK_RECEIVED, STATE_CLOSED)

    async def close(self, code=200) -> None:
        self.transport.write(frame.marshal(
            commands.Connection.Close(code, 'Client Requested', 0, 0), 0))
        self._set_state(STATE_CLOSE_SENT)
        await self._wait_on_state(STATE_CLOSED)

    @property
    def is_closed(self) -> bool:
        return self._state in [STATE_CLOSED, state.STATE_EXCEPTION]

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
            self._set_state(STATE_CLOSE_OK_SENT)
        elif value.reply_code in pamqp_exceptions.CLASS_MAPPING:
            self._set_state(
                STATE_CLOSE_OK_SENT,
                pamqp_exceptions.CLASS_MAPPING[value.reply_code](
                    value.reply_text))
        else:
            self._set_state(
                STATE_CLOSE_OK_SENT,
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
                STATE_CLOSED, exceptions.ClientNegotiationException())
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
        self._set_state(STATE_START_OK_SENT)

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
        self._set_state(STATE_TUNE_OK_SENT)
        self.transport.write(
            frame.marshal(commands.Connection.Open(self.virtual_host), 0))
        self._set_state(STATE_OPEN_SENT)
