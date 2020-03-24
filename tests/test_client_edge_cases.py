import asyncio
import os

from pamqp import base, body, commands, header

from aiorabbit import client, exceptions, message, state
from . import testing


class ClientCloseTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_close(self):
        await self.connect()
        await self.client.close()
        self.assertTrue(self.client.is_closed)

    @testing.async_test
    async def test_close_without_channel0(self):
        await self.connect()
        self.client._channel0 = None
        await self.client.close()
        self.assertTrue(self.client.is_closed)

    @testing.async_test
    async def test_close_when_in_exception(self):
        await self.connect()
        self.client._set_state(state.STATE_EXCEPTION)
        await self.client.close()
        self.assertTrue(self.client.is_closed)

    @testing.async_test
    async def test_close_when_in_exception_with_closed_channel(self):
        await self.connect()
        self.client._channel_open.clear()
        await self.client.close()
        self.assertTrue(self.client.is_closed)


class ChannelRotationTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_exceeds_max_channels(self):
        await self.connect()
        self.client._write(
            commands.Channel.Close(200, 'Client Requested', 0, 0))
        self.client._set_state(client.STATE_CHANNEL_CLOSE_SENT)
        await self.client._wait_on_state(client.STATE_CHANNEL_CLOSEOK_RECEIVED)
        self.client._channel = self.client._channel0.max_channels
        await self.client._open_channel()
        self.assertEqual(self.client._channel, 1)


class PopMessageTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_exceeds_max_channels(self):
        await self.connect()
        with self.assertRaises(RuntimeError):
            self.client._pop_message()


class BasicNackReceivedTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_nack_received(self):
        await self.connect()
        self.client._set_state(client.STATE_BASIC_PUBLISH_SENT)
        self.client._set_state(client.STATE_CONTENT_HEADER_SENT)
        self.client._set_state(client.STATE_CONTENT_BODY_SENT)
        self.client._on_frame(1, commands.Basic.Nack(10))
        self.assertSetEqual(self.client._nacks, {10})


class BasicRejectReceivedTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_nack_received(self):
        await self.connect()
        self.client._set_state(client.STATE_BASIC_PUBLISH_SENT)
        self.client._set_state(client.STATE_CONTENT_HEADER_SENT)
        self.client._set_state(client.STATE_CONTENT_BODY_SENT)
        self.client._on_frame(1, commands.Basic.Reject(10))
        self.assertSetEqual(self.client._rejects, {10})


class UnsupportedFrameOnFrameTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_delivery_unsupported_frame(self):
        await self.connect()
        msg_body = self.uuid4().encode('utf-8')
        self.client._message = message.Message(commands.Basic.Cancel('foo'))
        self.client._state = client.STATE_BASIC_DELIVER_RECEIVED
        self.client._on_frame(
            self.client._channel, header.ContentHeader(0, len(msg_body)))
        self.loop.call_soon(
            self.client._on_frame, self.client._channel,
            body.ContentBody(msg_body))
        with self.assertRaises(RuntimeError):
            await self.client._wait_on_state(state.STATE_EXCEPTION)

    @testing.async_test
    async def test_unsupported_frame(self):
        await self.connect()
        self.loop.call_soon(self.client._on_frame, 1, base.Frame())
        with self.assertRaises(RuntimeError):
            await self.client._wait_on_state(state.STATE_EXCEPTION)


class TimeoutOnConnectTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        self._old_uri = os.environ['RABBITMQ_URI']
        os.environ['RABBITMQ_URI'] = '{}?connection_timeout=0.001'.format(
            os.environ['RABBITMQ_URI'])
        super().setUp()

    def tearDown(self) -> None:
        os.environ['RABBITMQ_URI'] = self._old_uri
        super().tearDown()

    @testing.async_test
    async def test_timeout_error_on_connect_raises(self):
        with self.assertRaises(asyncio.TimeoutError):
            await self.connect()


class InvalidUsernameTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        self._old_uri = os.environ['RABBITMQ_URI']
        os.environ['RABBITMQ_URI'] = \
            os.environ['RABBITMQ_URI'].replace('guest', 'foo')
        super().setUp()

    def tearDown(self) -> None:
        os.environ['RABBITMQ_URI'] = self._old_uri
        super().tearDown()

    @testing.async_test
    async def test_error_on_connect_raises(self):
        with self.assertRaises(exceptions.AccessRefused):
            await self.connect()


class InvalidProtocolTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        self._old_uri = os.environ['RABBITMQ_URI']
        os.environ['RABBITMQ_URI'] = \
            os.environ['RABBITMQ_URI'].replace('amqp', 'amqps')
        super().setUp()

    def tearDown(self) -> None:
        os.environ['RABBITMQ_URI'] = self._old_uri
        super().tearDown()

    @testing.async_test
    async def test_error_on_connect_raises(self):
        with self.assertRaises(OSError):
            await self.connect()
