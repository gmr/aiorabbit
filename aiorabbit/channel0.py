# coding: utf-8
import asyncio
import platform
import typing

from pamqp import commands, constants, frame, header, heartbeat

from aiorabbit import exceptions, state
from aiorabbit.__version__ import version

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
STATE_STARTOK_SENT = 0x12
STATE_TUNE_RECEIVED = 0x13
STATE_TUNEOK_SENT = 0x14
STATE_OPEN_SENT = 0x15
STATE_OPENOK_RECEIVED = 0x16
STATE_HEARTBEAT_RECEIVED = 0x17
STATE_HEARTBEAT_SENT = 0x18
STATE_CLOSE_RECEIVED = 0x19
STATE_CLOSE_SENT = 0x20
STATE_CLOSEOK_RECEIVED = 0x21
STATE_CLOSEOK_SENT = 0x22
STATE_BLOCKED_RECEIVED = 0x23
STATE_UNBLOCKED_RECEIVED = 0x24

_STATE_MAP = {
    state.STATE_UNINITIALIZED: 'Uninitialized',
    state.STATE_EXCEPTION: 'Exception Raised',
    STATE_PROTOCOL_HEADER_SENT: 'Protocol Header Sent',
    STATE_START_RECEIVED: 'Start Received',
    STATE_STARTOK_SENT: 'StartOk Sent',
    STATE_TUNE_RECEIVED: 'Tune Received',
    STATE_TUNEOK_SENT: 'TuneOk Sent',
    STATE_OPEN_SENT: 'Open Sent',
    STATE_OPENOK_RECEIVED: 'OpenOk Received',
    STATE_HEARTBEAT_RECEIVED: 'Heartbeat Received',
    STATE_HEARTBEAT_SENT: 'Heartbeat Sent',
    STATE_CLOSE_RECEIVED: 'Connection Close Received',
    STATE_CLOSE_SENT: 'Connection Close Sent',
    STATE_CLOSEOK_SENT: 'Connection CloseOk Sent',
    STATE_CLOSEOK_RECEIVED: 'Connection CloseOk Received',
    STATE_BLOCKED_RECEIVED: 'Connection Blocked Received',
    STATE_UNBLOCKED_RECEIVED: 'Connection Unblocked Received'
}

_STATE_TRANSITIONS = {
    state.STATE_UNINITIALIZED: [STATE_PROTOCOL_HEADER_SENT],
    state.STATE_EXCEPTION: [STATE_CLOSE_SENT],
    STATE_PROTOCOL_HEADER_SENT: [STATE_START_RECEIVED],
    STATE_START_RECEIVED: [STATE_STARTOK_SENT],
    STATE_STARTOK_SENT: [STATE_TUNE_RECEIVED, STATE_CLOSE_RECEIVED],
    STATE_TUNE_RECEIVED: [STATE_TUNEOK_SENT],
    STATE_TUNEOK_SENT: [STATE_OPEN_SENT, STATE_CLOSE_RECEIVED],
    STATE_OPEN_SENT: [STATE_OPENOK_RECEIVED],
    STATE_OPENOK_RECEIVED: [
        STATE_BLOCKED_RECEIVED,
        STATE_HEARTBEAT_RECEIVED,
        STATE_CLOSE_RECEIVED,
        STATE_CLOSE_SENT],
    STATE_CLOSE_RECEIVED: [STATE_CLOSEOK_SENT],
    STATE_CLOSE_SENT: [STATE_CLOSEOK_RECEIVED],
    STATE_CLOSEOK_RECEIVED: [STATE_PROTOCOL_HEADER_SENT],
    STATE_CLOSEOK_SENT: [STATE_PROTOCOL_HEADER_SENT],
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
        STATE_CLOSE_SENT]
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
                 product: str,
                 on_remote_close: typing.Callable):
        super().__init__(loop)
        self.blocked = blocked
        self.max_channels = max_channels
        self.max_frame_size = constants.FRAME_MAX_SIZE
        self.properties: dict = {}
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timer: typing.Optional[asyncio.TimerHandle] = None
        self._last_error: typing.Tuple[int, typing.Optional[str]] = (0, None)
        self._last_heartbeat = 0
        self._locale = locale
        self._on_remote_close = on_remote_close
        self._password = password
        self._product = product
        self._transport: typing.Optional[asyncio.Transport] = None
        self._username = username
        self._virtual_host = virtual_host

    def process(self, value: COMMANDS) -> None:
        if isinstance(value, commands.Connection.Start):
            self._set_state(STATE_START_RECEIVED)
            self._process_start(value)
        elif isinstance(value, commands.Connection.Tune):
            self._set_state(STATE_TUNE_RECEIVED)
            self._process_tune(value)
        elif isinstance(value, commands.Connection.OpenOk):
            self._set_state(STATE_OPENOK_RECEIVED)
        elif isinstance(value, commands.Connection.Blocked):
            self._set_state(STATE_BLOCKED_RECEIVED)
            self.blocked.set()
        elif isinstance(value, commands.Connection.Unblocked):
            self._set_state(STATE_UNBLOCKED_RECEIVED)
            self.blocked.clear()
        elif isinstance(value, commands.Connection.Close):
            self._set_state(STATE_CLOSE_RECEIVED)
            self._transport.write(
                frame.marshal(commands.Connection.CloseOk(), 0))
            self._set_state(STATE_CLOSEOK_SENT)
            self._on_remote_close(value.reply_code, value.reply_text)
        elif isinstance(value, commands.Connection.CloseOk):
            self._set_state(STATE_CLOSEOK_RECEIVED)
        elif isinstance(value, heartbeat.Heartbeat):
            self._set_state(STATE_HEARTBEAT_RECEIVED)
            self._last_heartbeat = self._loop.time()
            self._transport.write(frame.marshal(heartbeat.Heartbeat(), 0))
            self._set_state(STATE_HEARTBEAT_SENT)
        else:
            self._set_state(state.STATE_EXCEPTION,
                            exceptions.AIORabbitException(
                                'Unsupported Frame Passed to Channel0'))

    async def open(self, transport: asyncio.Transport) -> bool:
        self._transport = transport
        self._transport.write(frame.marshal(header.ProtocolHeader(), 0))
        self._set_state(STATE_PROTOCOL_HEADER_SENT)
        result = await self._wait_on_state(
            STATE_OPENOK_RECEIVED, STATE_CLOSEOK_SENT)
        if self._heartbeat_interval:
            self._logger.debug('Checking for heartbeats every %2f seconds',
                               self._heartbeat_interval)
            self._heartbeat_timer = self._loop.call_later(
                self._heartbeat_interval, self._heartbeat_check)
        return result == STATE_OPENOK_RECEIVED

    async def close(self, code=200) -> None:
        self._heartbeat_timer.cancel()
        self._heartbeat_timer = None
        self._transport.write(frame.marshal(
            commands.Connection.Close(code, 'Client Requested', 0, 0), 0))
        self._set_state(STATE_CLOSE_SENT)
        await self._wait_on_state(STATE_CLOSEOK_RECEIVED)

    def reset(self):
        self._logger.debug('Resetting channel0')
        self._heartbeat_timer.cancel()
        self._heartbeat_timer = None
        self._reset_state(state.STATE_UNINITIALIZED)
        self._last_heartbeat = 0
        self._transport: typing.Optional[asyncio.Transport] = None
        self.properties: dict = {}

    @property
    def is_closed(self) -> bool:
        return self._state in [STATE_CLOSEOK_RECEIVED,
                               STATE_CLOSEOK_SENT,
                               state.STATE_EXCEPTION]

    def _heartbeat_check(self):
        threshold = self._loop.time() - (self._heartbeat_interval * 2)
        if self._last_heartbeat < threshold:
            msg = 'No heartbeat in {:2f} seconds'.format(
                self._loop.time() - self._last_heartbeat)
            self._logger.critical(msg)
            self._heartbeat_timer = None
            self._on_remote_close(599, 'Too many missed heartbeats')
        else:
            self._heartbeat_timer = self._loop.call_later(
                self._heartbeat_interval, self._heartbeat_check)

    @staticmethod
    def _negotiate(client: int, server: int) -> int:
        """Return the negotiated value between what the client has requested
        and the server has requested for how the two will communicate.

        """
        return min(client, server) or (client or server)

    def _process_start(self, value: commands.Connection.Start) -> None:
        if (value.version_major,
            value.version_minor) != (constants.VERSION[0],
                                     constants.VERSION[1]):
            self._logger.warning(
                'AMQP version error (received %i.%i, expected %r)',
                value.version_major, value.version_minor, constants.VERSION)
            self._transport.close()
            return self._set_state(
                state.STATE_EXCEPTION,
                exceptions.ClientNegotiationException(
                    'AMQP version error (received {}.{}, expected {})'.format(
                        value.version_major, value.version_minor,
                        constants.VERSION)))

        self.properties = dict(value.server_properties)
        for key in self.properties:
            if key == 'capabilities':
                for capability in self.properties[key]:
                    self._logger.debug(
                        'Server supports %s: %r',
                        capability, self.properties[key][capability])
            else:
                self._logger.debug('Server %s: %r', key, self.properties[key])
        self._transport.write(frame.marshal(
            commands.Connection.StartOk(
                client_properties={
                    'product': self._product,
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
                response='\0{}\0{}'.format(self._username, self._password),
                locale=self._locale), 0))
        self._set_state(STATE_STARTOK_SENT)

    def _process_tune(self, value: commands.Connection.Tune) -> None:
        self.max_channels = self._negotiate(
            self.max_channels, value.channel_max)
        self.max_frame_size = self._negotiate(
            self.max_frame_size, value.frame_max)
        if self._heartbeat_interval is None:
            self._heartbeat_interval = value.heartbeat
        elif not self._heartbeat_interval and not value.heartbeat:
            self._heartbeat_interval = 0
        self._transport.write(frame.marshal(
            commands.Connection.TuneOk(
                self.max_channels, self.max_frame_size,
                self._heartbeat_interval), 0))
        self._set_state(STATE_TUNEOK_SENT)
        self._transport.write(
            frame.marshal(commands.Connection.Open(self._virtual_host), 0))
        self._set_state(STATE_OPEN_SENT)
