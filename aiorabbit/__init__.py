# coding: utf-8
import asyncio
import contextlib
import logging
import ssl
import typing

from aiorabbit import exceptions
from aiorabbit.__version__ import version

DEFAULT_LOCALE = 'en-US'
DEFAULT_PRODUCT = 'aiorabbit/{}'.format(version)
DEFAULT_URL = 'amqp://guest:guest@localhost'

LOGGER = logging.getLogger('aiorabbit')


@contextlib.asynccontextmanager
async def connect(url: str = DEFAULT_URL,
                  locale: str = DEFAULT_LOCALE,
                  product: str = DEFAULT_PRODUCT,
                  loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                  on_return: typing.Optional[typing.Callable] = None,
                  ssl_context: typing.Optional[ssl.SSLContext] = None):
    """Asynchronous :ref:`context-manager <python:typecontextmanager>` that
    connects to RabbitMQ, returning a connected
    :class:`~aiorabbit.client.Client` as the target.

    .. code-block:: python3
       :caption: Example Usage

       async with aiorabbit.connect(RABBITMQ_URL) as client:
            await client.exchange_declare('test', 'topic')

    :param url: The URL to connect to RabbitMQ with
    :param locale: The locale for the connection, default `en-US`
    :param product: The product name for the connection, default `aiorabbit`
    :param loop: Optional :mod:`asyncio` event loop to use
    :param on_return: An optional callback method to be invoked if the server
        returns a published method. Can also be set using the
        :meth:`~Client.register_basic_return_callback` method.
    :param ssl_context: Optional :class:`ssl.SSLContext` for the connection

    """
    from aiorabbit import client

    rmq_client = client.Client(
        url, locale, product, loop, on_return, ssl_context)
    await rmq_client.connect()
    try:
        yield rmq_client
    finally:
        if not rmq_client.is_closed:
            await rmq_client.close()

__all__ = [
    'client',
    'connect',
    'DEFAULT_PRODUCT',
    'DEFAULT_LOCALE',
    'DEFAULT_URL',
    'exceptions',
    'message',
    'types',
    'version'
]
