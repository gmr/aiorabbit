import asyncio
import functools
import logging
import os
import unittest

from aiorabbit import client

LOGGER = logging.getLogger(__name__)


def async_test(*func):
    if func:
        @functools.wraps(func[0])
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            LOGGER.debug('Starting test')
            loop.run_until_complete(func[0](*args, **kwargs))
            LOGGER.debug('Test completed')
        return wrapper


class AsyncTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_debug(True)
        self.timeout = int(os.environ.get('ASYNC_TIMEOUT', '5'))
        self.timeout_handle = self.loop.call_later(
            self.timeout, self.on_timeout)

    def tearDown(self):
        LOGGER.debug('In AsyncTestCase.tearDown')
        if not self.timeout_handle.cancelled():
            self.timeout_handle.cancel()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        if self.loop.is_running:
            self.loop.close()

    def on_timeout(self):
        self.loop.stop()
        raise TimeoutError(
            'Test duration exceeded {} seconds'.format(self.timeout))


class ClientTestCase(AsyncTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.rabbitmq_url = os.environ['RABBITMQ_URI']
        self.client = client.Client(self.rabbitmq_url, loop=self.loop)

    def tearDown(self) -> None:
        LOGGER.debug('In ClientTestCase.tearDown')
        if not self.client.is_closed:
            LOGGER.debug('Closing on tearDown')
            self.loop.run_until_complete(self.close())
        super().tearDown()

    def assert_state(self, *state):
        self.assertIn(
            self.client.state, [self.client.STATE_MAP[s] for s in state])

    async def connect(self):
        LOGGER.debug('Client connecting')
        self.assert_state(client.STATE_DISCONNECTED, client.STATE_CLOSED)
        await self.client.connect()
        self.assert_state(client.STATE_CHANNEL_OPENOK_RECEIVED)

    async def close(self):
        LOGGER.debug('Client closing')
        await self.client.close()
        self.assert_state(client.STATE_CLOSED)
