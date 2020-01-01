"""
AsyncIO RabbitMQ Client
=======================

"""
import asyncio
import logging
import socket
import typing
from urllib import parse

from pamqp import base, body, header, heartbeat
import yarl

from aiorabbit import (channel0,
                       DEFAULT_LOCALE,
                       DEFAULT_PRODUCT,
                       DEFAULT_URL,
                       protocol,
                       state)

LOGGER = logging.getLogger(__name__)


Frame = typing.Union[base.Frame,
                     body.ContentBody,
                     header.ContentHeader,
                     heartbeat.Heartbeat]


class Client(state.StateManager):
    """RabbitMQ Client"""
    STATE_UNINITIALIZED = 0x00
    STATE_DISCONNECTED = 0x01
    STATE_CONNECTING = 0x02
    STATE_CONNECTED = 0x03
    STATE_OPENING = 0x04
    STATE_OPENED = 0x05
    STATE_CLOSING = 0x06
    STATE_CLOSED = 0x07

    STATE_MAP = {
        0x00: 'Uninitialized',
        0x01: 'Disconnected',
        0x02: 'Connecting',
        0x03: 'Connected',
        0x04: 'Opening',
        0x05: 'Opened',
        0x06: 'Closing',
        0x07: 'Closed'
    }

    STATE_TRANSITIONS = {
        STATE_UNINITIALIZED: {STATE_DISCONNECTED},
        STATE_DISCONNECTED: {STATE_CONNECTING},
        STATE_CONNECTING: {STATE_DISCONNECTED, STATE_CONNECTED},
        STATE_CONNECTED: {STATE_OPENING, STATE_CLOSING, STATE_CLOSED},
        STATE_OPENING: {STATE_OPENED, STATE_CLOSED},
        STATE_OPENED: {STATE_CLOSING, STATE_CLOSED},
        STATE_CLOSING: {STATE_CLOSED}
    }

    def __init__(self,
                 url: str = DEFAULT_URL,
                 locale: str = DEFAULT_LOCALE,
                 product: str = DEFAULT_PRODUCT,
                 loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop or asyncio.get_running_loop())
        self._blocked = asyncio.Event()
        self._connected = asyncio.Event()
        self._transport: typing.Optional[asyncio.Transport] = None
        self._protocol: typing.Optional[asyncio.Protocol] = None
        self._url = yarl.URL(url)
        self._set_state(self.STATE_DISCONNECTED)
        self._channel0 = channel0.Channel0(
            self._blocked, self._url.user, self._url.password,
            self._url.path[1:], self._url.query.get('heartbeat'), locale,
            self._loop, int(self._url.query.get('channel_max', '32768')),
            product)

    async def __aenter__(self):
        await self._connect()

    async def __aexit__(self, exc_type, exc, tb):
        if not exc_type:
            await self.close()

    async def connect(self) -> typing.NoReturn:
        """Connect to the RabbitMQ Server"""
        await self._connect()
        await self._wait_on_state(self.STATE_OPENED)

    async def close(self) -> typing.NoReturn:
        self._set_state(self.STATE_CLOSING)
        await self._channel0.close()
        self._transport.close()
        self._set_state(self.STATE_CLOSED)

    async def _connect(self) -> typing.NoReturn:
        self._set_state(self.STATE_CONNECTING)
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
        except asyncio.TimeoutError:
            self._set_state(self.STATE_DISCONNECTED)
            raise
        self._set_state(self.STATE_CONNECTED)

    async def _on_connected(self):
        self._set_state(self.STATE_OPENING)
        await self._channel0.open(self._transport)
        self._set_state(self.STATE_OPENED)

    async def _on_disconnected(self):
        LOGGER.critical('Connection Lost')
        self._set_state(self.STATE_CLOSED)

    async def _on_frame(self, channel: int, value: Frame) -> typing.NoReturn:
        if channel == 0:
            await self._channel0.process(value)
        else:
            raise RuntimeError('Main commands not supported yet')

    @property
    def _connect_timeout(self):
        temp = self._url.query.get('connection_timeout')
        return socket.getdefaulttimeout() if temp is None else float(temp)
