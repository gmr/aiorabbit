import asyncio
import logging
import os
from unittest import mock

from pamqp import commands

import aiorabbit
from aiorabbit import client, exceptions
from tests import testing

LOGGER = logging.getLogger(__name__)


class ContextManagerTestCase(testing.AsyncTestCase):

    @testing.async_test
    async def test_context_manager_open(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as client_:
            await client_.confirm_select()
            self.assertEqual(client_._state,
                             client.STATE_CONFIRM_SELECTOK_RECEIVED)
        self.assertEqual(client_._state, client.STATE_CLOSED)

    @testing.async_test
    async def test_context_manager_exception(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as client_:
            await client_.confirm_select()
            with self.assertRaises(RuntimeError):
                await client_.confirm_select()
        self.assertEqual(client_._state, client.STATE_CLOSED)

    @testing.async_test
    async def test_context_manager_remote_close(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as client_:
            LOGGER.debug('Sending admin shutdown frame')
            client_._on_frame(
                0, commands.Connection.Close(200, 'Admin Shutdown'))
            while not client_.is_closed:
                await asyncio.sleep(0.1)
        self.assertEqual(client_._state, client.STATE_CLOSED)

    @testing.async_test
    async def test_context_manager_already_closed_on_exit(self):
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as client_:
            self.assertFalse(client_.is_closed)
            client_._state = client.STATE_CLOSED
        self.assertTrue(client_.is_closed)
        async with aiorabbit.connect(
                os.environ['RABBITMQ_URI'], loop=self.loop) as client_:
            self.assertFalse(client_.is_closed)
        self.assertTrue(client_.is_closed)


class IntegrationTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_recycling(self):
        await self.connect()
        self.assertEqual(self.client._channel, 1)
        await self.close()
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
        with self.assertRaises(exceptions.CommandInvalid):
            self.client._write(
                commands.Connection.UpdateSecret('foo', 'bar'))
            await self.client._wait_on_state(
                client.STATE_UPDATE_SECRETOK_RECEIVED)


class ReconnectPublisherConfirmsTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_confirm_select_already_invoked_on_reconnect(self):
        await self.connect()
        await self.client.confirm_select()
        self.assertTrue(self.client._publisher_confirms)
        with self.assertRaises(exceptions.CommandInvalid):
            await self.client.exchange_declare(self.uuid4(), self.uuid4())
        self.assertTrue(self.client._publisher_confirms)


class QosPrefetchTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_qos(self):
        await self.connect()
        await self.client.qos_prefetch(100, False)
        await self.client.qos_prefetch(125, True)

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.qos_prefetch('foo')
        with self.assertRaises(TypeError):
            await self.client.qos_prefetch(0, 'foo')


class ConsumeTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.queue = self.uuid4()
        self.exchange = 'amq.topic'

    @testing.async_test
    async def test_consume(self):
        await self.connect()
        await self.client.queue_declare(self.queue)
        await self.client.queue_bind(self.queue, self.exchange, '#')
        await self.client.qos_prefetch(1, True)
        messages = [self.uuid4().encode('utf-8') for _offset in range(0, 5)]
        for message in messages:
            await self.client.publish(self.exchange, self.queue, message)

        msgs, _consumers = await self.client.queue_declare(self.queue)
        while msgs < len(messages):
            await asyncio.sleep(0.5)
            msgs, consumers = await self.client.queue_declare(self.queue)

        consumer = self.client.consume(self.queue)
        async for message in consumer:
            messages.remove(message.body)
            await self.client.basic_ack(message.delivery_tag)
            if not messages:
                await consumer.aclose()

        msgs, _consumers = await self.client.queue_declare(self.queue)
        self.assertEqual(msgs, 0)
