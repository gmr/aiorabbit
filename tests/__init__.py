import asyncio
import functools
import os
import unittest

from aiorabbit import client


def setup_module():
    """Ensure the test environment variables are set"""
    try:
        with open('build/test-environment') as f:
            for line in f:
                if line.startswith('export '):
                    line = line[7:]
                name, _, value = line.strip().partition('=')
                os.environ[name] = value
    except IOError:
        pass


def async_test(*func):
    if func:
        @functools.wraps(func[0])
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(func[0](*args, **kwargs))
        return wrapper


class AsyncTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.rabbitmq_url = os.environ['RABBITMQ_URI']
        self.client = client.Client(self.rabbitmq_url, loop=self.loop)
        self.timeout = int(os.environ.get('ASYNC_TIMEOUT', '3'))
        self.timeout_handle = self.loop.call_later(
            self.timeout, self.on_timeout)

    def tearDown(self):
        if not self.timeout_handle.cancelled():
            self.timeout_handle.cancel()

    def assert_state(self, state):
        self.assertEqual(self.client.state, self.client.STATE_MAP[state])

    def on_timeout(self):
        self.loop.stop()
        raise TimeoutError(
            'Test duration exceeded {} seconds'.format(self.timeout))

    async def connect(self):
        self.assert_state(self.client.STATE_DISCONNECTED)
        await self.client.connect()
        self.assert_state(self.client.STATE_CHANNEL_OPENOK_RECEIVED)

    async def close(self):
        await self.client.close()
        self.assert_state(self.client.STATE_CLOSED)
