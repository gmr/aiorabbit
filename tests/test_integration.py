import asyncio
import os
import unittest
from unittest import mock

from aiorabbit import client


class IntegrationTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.rabbitmq_url = os.environ['RABBITMQ_URI']
        self.client = client.Client(self.rabbitmq_url, loop=self.loop)
        self.timeout_handle = self.loop.call_later(3, self.on_timeout)
        # self.loop.set_exception_handler(self.on_exception)

    def tearDown(self):
        if not self.timeout_handle.cancelled():
            self.timeout_handle.cancel()

    def assert_state(self, state):
        self.assertEqual(self.client.state, self.client.STATE_MAP[state])

    def on_exception(self, loop, context):
        self.timeout_handle.cancel()
        self.loop.stop()
        raise context['exception']

    def on_timeout(self):
        self.loop.stop()
        raise TimeoutError('Test duration exceeded 3 seconds')

    async def connect(self):
        self.assert_state(self.client.STATE_DISCONNECTED)
        await self.client.connect()
        self.assert_state(self.client.STATE_CHANNEL_OPENOK_RECEIVED)
        await self.client.confirm_select()
        self.assert_state(self.client.STATE_CONFIRM_SELECTOK_RECEIVED)
        await self.client.close()
        self.assert_state(self.client.STATE_CLOSED)

    def test_client(self):
        self.loop.run_until_complete(self.connect())

    async def close_error(self):
        raise RuntimeError('Faux Exception')

    def test_connect_error(self):
        with mock.patch.object(self.client, 'close') as close:
            close.side_effect = self.close_error
            with self.assertRaises(RuntimeError):
                self.loop.run_until_complete(self.connect())
