"""
AsyncIO RabbitMQ Client
=======================

"""
import asyncio
import logging
import time
import typing

from pamqp import body, commands, exceptions, frame, header, heartbeat
import yarl

from aiorabbit import state

LOGGER = logging.getLogger(__name__)
DEFAULT_URL = 'amqp://guest:guest@localhost:5672/%2f'


class Client(state.StateManager):
    """RabbitMQ Client"""

    DEFAULT_LOCALE = 'en-US'

    STATE_UNINITIALIZED: typing.Final[int] = 0x00
    STATE_DISCONNECTED: typing.Final[int]  = 0x01
    STATE_CONNECTING: typing.Final[int]  = 0x02
    STATE_CONNECTED: typing.Final[int]  = 0x02
    STATE_OPENING_CHANNEL = 0x04
    STATE_CHANNEL_OPEN = 0x04
    STATE_CHANNEL_CLOSED = 0x04
    STATE_CLOSING = 0x02
    STATE_CLOSED = 0x02

    STATE: dict = {
        0x00: 'Uninitialized',
        0x01: 'Disconnected',
        0x02: 'Connecting'
    }

    STATE_MAP: dict = {
        STATE_UNINITIALIZED: {STATE_DISCONNECTED},
        STATE_DISCONNECTED: {STATE_CONNECTING},
        STATE_CHANNEL_OPEN: {STATE_CHANNEL_CLOSED},
        STATE_CLOSING: {STATE_DISCONNECTED}
    }

    def __init__(self, url: str = DEFAULT_URL,
                 loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop or asyncio.get_running_loop())
        self._pending_frames = asyncio.Queue(loop=self._loop)
        self._reader: typing.Optional[asyncio.StreamReader] = None
        self._url = yarl.URL(url)
        self._writer: typing.Optional[asyncio.StreamWriter] = None
        self._set_state(self.STATE_DISCONNECTED)

    def __aenter__(self):
        await self._connect()

    async def __aexit__(self, exc_type, exc, tb):
        if not exc_type:
            await self.close()
        pass

    async def connect(self) -> typing.NoReturn:
        """Connect to the RabbitMQ Server"""
        await self._connect()

    async def close(self) -> typing.NoReturn:
        self._set_state(self.STATE_CLOSING)
        self._writer.close()

    async def _connect(self) -> typing.NoReturn:
        self._set_state(self.STATE_CONNECTING)
        self._reader, self._writer = await asyncio.open_connection(
            self._url.host, self._url.port, loop=self._loop,
            ssl=self._url.scheme == 'amqps')





    def _write_frame(self, channel: int, value: typing.Union[
            body.ContentBody, commands.base.Frame, header.ProtocolHeader,
            header.ContentHeader, heartbeat.Heartbeat]) -> typing.NoReturn:
        self._writer.write(frame.marshall(value, channel))
