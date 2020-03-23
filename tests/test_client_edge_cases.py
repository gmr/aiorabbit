import asyncio
import os
from unittest import mock

from pamqp import base, commands

from aiorabbit import client, message, state
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


class BasicConsumeTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_consume_already_registered(self):

        def on_message(_msg):
            pass

        await self.connect()

        ctag = self.uuid4()
        self.client._consumers[ctag] = on_message
        self.client._state = client.STATE_BASIC_CONSUME_SENT
        with mock.patch.object(self.client, '_write') as write:
            write.side_effect = lambda x: self.loop.call_soon(
                self.client._on_frame, 1, commands.Basic.ConsumeOk(ctag))
            with self.assertRaises(RuntimeError):
                await self.client.basic_consume('foo', callback=on_message)


class OnBasicDeliverTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_on_basic_deliver_raises(self):
        await self.connect()
        with self.assertRaises(RuntimeError):
            self.client._on_basic_deliver(
                message.Message(commands.Basic.Deliver('foo', 1)))


class OnBasicReturnTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_on_basic_return_sync(self):
        await self.connect()

        def on_basic_return(_msg):
            self.test_finished.set()

        self.client.register_message_return_callback(on_basic_return)
        self.client._on_basic_return(
            message.Message(commands.Basic.Return(404, 'Not Found')))
        await self.test_finished.wait()

    @testing.async_test
    async def test_async_on_basic_return_async(self):
        await self.connect()

        async def on_basic_return(_msg):
            await asyncio.sleep(1)
            self.test_finished.set()

        self.client.register_message_return_callback(on_basic_return)
        self.client._on_basic_return(
            message.Message(commands.Basic.Return(404, 'Not Found')))
        await self.test_finished.wait()
