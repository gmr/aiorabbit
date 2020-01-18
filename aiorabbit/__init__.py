"""
aiorabbit
=========
"""
import asyncio
import contextlib
import logging
import typing

version = '0.1.0a1'

DEFAULT_LOCALE = 'en-US'
DEFAULT_PRODUCT = 'aiorabbit'
DEFAULT_URL = 'amqp://guest:guest@localhost:5672/%2f'

LOGGER = logging.getLogger('aiorabbit')


@contextlib.asynccontextmanager
async def connect(url: str = DEFAULT_URL,
                  locale: str = DEFAULT_LOCALE,
                  product: str = DEFAULT_PRODUCT,
                  loop: typing.Optional[asyncio.AbstractEventLoop] = None):
    """Connect to RabbitMQ, returning a :py:class:`asyncio.client.Client`
    instance.

    :param url: The URL to connect to RabbitMQ with
    :param locale: The locale for the connection, default `en-US`
    :param product: The product name for the connection, default `aiorabbit`
    :param loop: Optional asyncio Loop to use

    """
    from aiorabbit import client

    rabbitmq = client.Client(url, locale, product, loop)
    await rabbitmq.connect()
    try:
        yield rabbitmq
    finally:
        if not rabbitmq.closed:
            await rabbitmq.close()
        del client


__all__ = [
    'client',
    'connect',
    'DEFAULT_PRODUCT',
    'DEFAULT_LOCALE',
    'DEFAULT_URL',
    'exceptions',
    'version'
]
