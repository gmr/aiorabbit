# coding: utf-8
import asyncio
import logging
import typing

from pamqp import exceptions, frame

LOGGER = logging.getLogger(__name__)


class AMQP(asyncio.Protocol):
    """AMQP Protocol adapter for AsyncIO"""
    def __init__(self,
                 on_connected: callable,
                 on_disconnected: callable,
                 on_frame_received: callable):
        self.buffer: bytes = b''
        self.loop = asyncio.get_running_loop()
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        self.on_frame_received = on_frame_received
        self.transport: typing.Optional[asyncio.Transport] = None

    def connection_made(self, transport) -> None:
        self.transport = transport
        self.on_connected()

    def connection_lost(self, exc: typing.Optional[Exception]) -> None:
        self.on_disconnected(exc)

    def data_received(self, data: bytes) -> None:
        self.buffer += data
        while self.buffer:
            try:
                count, channel, value = frame.unmarshal(self.buffer)
            except exceptions.UnmarshalingException as error:
                LOGGER.warning('Failed to unmarshal a frame: %r', error)
                LOGGER.debug('Bad frame: %r', self.buffer)
                break
            else:
                self.buffer = self.buffer[count:]
                self.loop.call_soon(self.on_frame_received, channel, value)

    def pause_writing(self) -> None:  # pragma: nocover
        LOGGER.critical('Should pause writing, but it is not implemented')

    def resume_writing(self) -> None:  # pragma: nocover
        LOGGER.info('Can resume writing, but it is not implemented')
