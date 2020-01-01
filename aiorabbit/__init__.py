"""
aiorabbit
=========
"""
from __future__ import annotations

import asyncio
import typing

version: typing.Final[str] = '0.1.0'

DEFAULT_LOCALE: typing.Final[str] = 'en-US'
DEFAULT_PRODUCT: typing.Final[str] = 'aiorabbitmq'
DEFAULT_URL: typing.Final[str] = 'amqp://guest:guest@localhost:5672/%2f'


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
