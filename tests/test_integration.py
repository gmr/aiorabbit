import asyncio
import os
import unittest

from aiorabbit import client


class IntegrationTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.rabbitmq_url = os.environ['RABBITMQ_URI']
        self.client = client.Client(self.rabbitmq_url, loop=self.loop)

    def assert_state(self, state):
        self.assertEqual(self.client.state, self.client.STATE_MAP[state])

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
        raise ValueError
