import asyncio
import logging
import os
from unittest import mock

from pamqp import commands
from pamqp import exceptions as pamqp_exceptions

import aiorabbit
from aiorabbit import client, exceptions, state

from . import testing


class ContextManagerTestCase(testing.AsyncTestCase):

    @testing.async_test
    async def test_context_manager_open(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as c:
            await c.confirm_select()
            self.assertEqual(c._state, client.STATE_CONFIRM_SELECTOK_RECEIVED)
        self.assertEqual(c._state, client.STATE_CLOSED)

    @testing.async_test
    async def test_context_manager_exception(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as c:
            await c.confirm_select()
            with self.assertRaises(RuntimeError):
                await c.confirm_select()
            logging.getLogger(__name__).debug('Should close with swallowing the exception')
        self.assertEqual(c._state, client.STATE_CLOSED)


class IntegrationTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_recycling(self):
        await self.connect()
        await self.close()
        self.client._channel = self.client._channel0.max_channels
        await self.connect()
        self.assertEqual(self.client._channel, 1)
        await self.close()

    @testing.async_test
    async def test_double_close(self):
        await self.connect()
        await self.close()
        await self.close()

    @testing.async_test
    async def test_confirm_select(self):
        await self.connect()
        await self.client.confirm_select()
        self.assert_state(client.STATE_CONFIRM_SELECTOK_RECEIVED)
        await self.close()

    @testing.async_test
    async def test_connect_timeout(self):
        with mock.patch.object(self.loop, 'create_connection') as create_conn:
            create_conn.side_effect = asyncio.TimeoutError()
            with self.assertRaises(asyncio.TimeoutError):
                await self.connect()

    @testing.async_test
    async def test_client_close_error(self):
        await self.connect()
        with mock.patch.object(self.client, 'close') as close:
            close.side_effect = RuntimeError('Faux Exception')
            with self.assertRaises(RuntimeError):
                await self.close()

    @testing.async_test
    async def test_update_secret_raises(self):
        await self.connect()
        with self.assertRaises(pamqp_exceptions.AMQPCommandInvalid):
            self.client._write(
                commands.Connection.UpdateSecret('foo', 'bar'))
            await self.client._wait_on_state(
                client.STATE_UPDATE_SECRETOK_RECEIVED)
