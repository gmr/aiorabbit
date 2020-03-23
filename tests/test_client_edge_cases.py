from pamqp import base, commands

from aiorabbit import client, state
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


class TestChannelRotation(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_exceeds_max_channels(self):
        await self.connect()
        self.client._write(commands.Channel.Close(200, 'Client Requested'))
        self.client._set_state(client.STATE_CHANNEL_CLOSE_SENT)
        await self.client._wait_on_state(client.STATE_CHANNEL_CLOSEOK_RECEIVED)
        self.client._channel = self.client._channel0.max_channels
        await self.client._open_channel()
        self.assertEqual(self.client._channel, 1)


class TestPopMessage(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_exceeds_max_channels(self):
        await self.connect()
        with self.assertRaises(RuntimeError):
            self.client._pop_message()


class TestBasicNackReceived(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_nack_received(self):
        await self.connect()
        self.client._set_state(client.STATE_BASIC_PUBLISH_SENT)
        self.client._set_state(client.STATE_CONTENT_HEADER_SENT)
        self.client._set_state(client.STATE_CONTENT_BODY_SENT)
        self.client._on_frame(1, commands.Basic.Nack(10))
        self.assertSetEqual(self.client._nacks, {10})


class TestBasicRejectReceived(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_nack_received(self):
        await self.connect()
        self.client._set_state(client.STATE_BASIC_PUBLISH_SENT)
        self.client._set_state(client.STATE_CONTENT_HEADER_SENT)
        self.client._set_state(client.STATE_CONTENT_BODY_SENT)
        self.client._on_frame(1, commands.Basic.Reject(10))
        self.assertSetEqual(self.client._rejects, {10})


class TestUnsupportedFrameOnFrame(testing.ClientTestCase):

    @testing.async_test
    async def test_unsupported_frame(self):
        await self.connect()
        self.loop.call_soon(self.client._on_frame, 1, base.Frame())
        with self.assertRaises(RuntimeError):
            await self.client._wait_on_state(state.STATE_EXCEPTION)
