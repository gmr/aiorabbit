import asyncio
import os

from pamqp import base, commands

from aiorabbit import channel0, client, exceptions, state
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

    @testing.async_test
    async def test_contemporaneous_double_close(self):
        await self.connect()
        await asyncio.gather(
            self.client.close(),
            self.client.close())
        self.assertTrue(self.client.is_closed)


class ChannelRotationTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_channel_exceeds_max_channels(self):
        await self.connect()
        self.client._write_frames(
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
        delivery_tag = 10
        self.client._delivery_tags[delivery_tag] = asyncio.Event()
        self.client._set_state(client.STATE_MESSAGE_PUBLISHED)
        self.client._on_frame(1, commands.Basic.Nack(delivery_tag))
        await self.client._delivery_tags[delivery_tag].wait()
        self.assertFalse(self.client._confirmation_result[delivery_tag])


class BasicRejectReceivedTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_nack_received(self):
        await self.connect()
        delivery_tag = 10
        self.client._delivery_tags[delivery_tag] = asyncio.Event()
        self.client._set_state(client.STATE_MESSAGE_PUBLISHED)
        self.client._on_frame(1, commands.Basic.Reject(delivery_tag))
        await self.client._delivery_tags[delivery_tag].wait()
        self.assertFalse(self.client._confirmation_result[delivery_tag])


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
        os.environ['RABBITMQ_URI'] = '{}?connection_timeout=0.000001'.format(
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


class InvalidVHostTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        self._old_uri = os.environ['RABBITMQ_URI']
        os.environ['RABBITMQ_URI'] = \
            os.environ['RABBITMQ_URI'].replace('%2f', 'invalid')
        super().setUp()

    def tearDown(self) -> None:
        os.environ['RABBITMQ_URI'] = self._old_uri
        super().tearDown()

    @testing.async_test
    async def test_error_on_connect_raises(self):
        with self.assertRaises(exceptions.NotAllowed):
            await self.connect()


class ReconnectAfterWedgedStateTestCase(testing.ClientTestCase):
    """A client that is closed but left in a non-idle state must still be
    able to reconnect. See https://github.com/gmr/aiorabbit/issues/24

    """
    @testing.async_test
    async def test_reconnect_after_disconnect_skips_exception_state(self):
        """``_on_disconnected`` is a no-op when ``is_closed`` is already
        ``True``, leaving ``_state`` wherever the last operation left it.

        """
        await self.connect()
        self.client._set_state(client.STATE_MESSAGE_PUBLISHED)
        self.client._channel0._state = channel0.STATE_CLOSEOK_SENT
        self.assertTrue(self.client.is_closed)
        self.client._on_disconnected(None)
        self.assert_state(client.STATE_MESSAGE_PUBLISHED)
        await self.client.connect()
        self.assert_state(client.STATE_CHANNEL_OPENOK_RECEIVED)

    @testing.async_test
    async def test_reconnect_after_remote_close_exception(self):
        """``STATE_EXCEPTION`` has no transition to ``STATE_CONNECTING``"""
        await self.connect()
        self.client._on_remote_close(320, 'CONNECTION_FORCED - broker forced')
        self.assert_state(state.STATE_EXCEPTION)
        self.assertTrue(self.client.is_closed)
        await self.client.connect()
        self.assert_state(client.STATE_CHANNEL_OPENOK_RECEIVED)

    @testing.async_test
    async def test_reconnect_from_state_without_path_to_closed(self):
        """``STATE_CONTENT_HEADER_RECEIVED`` can only transition to
        ``STATE_CONTENT_BODY_RECEIVED``, so ``close()`` can not repair it.

        """
        await self.connect()
        self.client._set_state(client.STATE_BASIC_DELIVER_RECEIVED)
        self.client._set_state(client.STATE_CONTENT_HEADER_RECEIVED)
        self.client._channel0._state = channel0.STATE_CLOSEOK_SENT
        self.assertTrue(self.client.is_closed)
        await self.client.connect()
        self.assert_state(client.STATE_CHANNEL_OPENOK_RECEIVED)
