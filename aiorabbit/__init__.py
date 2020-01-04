"""
aiorabbit
=========
"""
import asyncio
import typing

version = '0.1.0'

DEFAULT_LOCALE = 'en-US'
DEFAULT_PRODUCT = 'aiorabbitmq'
DEFAULT_URL = 'amqp://guest:guest@localhost:5672/%2f'


async def connect(url: str = DEFAULT_URL,
                  locale: str = DEFAULT_LOCALE,
                  product: str = DEFAULT_PRODUCT,
                  loop: typing.Optional[asyncio.AbstractEventLoop] = None):
    """Connect to RabbitMQ, returning a :py:class:`asyncio.client.Client`
    instance.

    """
    import aiorabbit.client

    client = aiorabbit.client.Client(url, locale, product, loop)
    await client.connect()
    return client


__all__ = [
    'client',
    'connect',
    'DEFAULT_PRODUCT',
    'DEFAULT_LOCALE',
    'DEFAULT_URL',
    'exceptions',
    'version'
]
