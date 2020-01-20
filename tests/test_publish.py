import asyncio
import logging
import uuid

from pamqp import constants

from aiorabbit import client
from . import testing

LOGGER = logging.getLogger(__name__)


class PublishingArgumentsTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_bad_exchange(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.publish(1, 'foo', b'bar')

    @testing.async_test
    async def test_bad_routing_key(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.publish('foo', 2, b'bar')

    @testing.async_test
    async def test_bad_message_body(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.publish('foo', 'bar', {'foo': 'bar'})

    @testing.async_test
    async def test_bad_booleans(self):
        await self.connect()
        for field in ['mandatory', 'immediate']:
            with self.assertRaises(TypeError):
                kwargs = {field: 'qux'}
                await self.client.publish('foo', 'bar', b'baz', **kwargs)

    @testing.async_test
    async def test_bad_strs(self):
        await self.connect()
        for field in ['app_id', 'content_encoding', 'content_type',
                      'correlation_id', 'expiration', 'message_id',
                      'message_type', 'reply_to', 'user_id']:
            LOGGER.debug('testing %s with non-string value', field)
            with self.assertRaises(TypeError):
                kwargs = {field: 32768}
                await self.client.publish('foo', 'bar', b'baz', **kwargs)

    @testing.async_test
    async def test_bad_ints(self):
        await self.connect()
        for field in ['delivery_mode', 'priority']:
            with self.assertRaises(TypeError):
                kwargs = {field: 'qux'}
                await self.client.publish('foo', 'bar', b'baz', **kwargs)

    @testing.async_test
    async def test_bad_delivery_mode(self):
        await self.connect()
        with self.assertRaises(ValueError):
            await self.client.publish(
                'foo', 'bar', b'baz', delivery_mode=-1)
        with self.assertRaises(ValueError):
            await self.client.publish(
                'foo', 'bar', b'baz', delivery_mode=3)

    @testing.async_test
    async def test_bad_headers(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.publish('foo', 'bar', b'baz', headers=1)

    @testing.async_test
    async def test_bad_priority(self):
        await self.connect()
        with self.assertRaises(ValueError):
            await self.client.publish(
                'foo', 'bar', b'baz', priority=-1)
        with self.assertRaises(ValueError):
            await self.client.publish(
                'foo', 'bar', b'baz', priority=32768)

    @testing.async_test
    async def test_bad_timestamp(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.publish(
                'foo', 'bar', b'baz', timestamp=1579390178)


class PublishingTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.test_finished = asyncio.Event()
        self.exchange = ''
        self.routing_key = str(uuid.uuid4())
        self.body = bytes(uuid.uuid4().hex, 'latin-1')

    @testing.async_test
    async def test_minimal_publish(self):
        await self.connect()
        await self.client.publish(self.exchange, self.routing_key, self.body)

    @testing.async_test
    async def test_minimal_publish_with_empty_routing_key(self):
        await self.connect()
        await self.client.publish(self.exchange, '', self.body)

    @testing.async_test
    async def test_minimal_publish_with_str_body(self):
        await self.connect()
        await self.client.publish(
            self.exchange, self.routing_key, str(self.body))

    @testing.async_test
    async def test_minimal_publish_with_large_body(self):
        body = b'-'.join([uuid.uuid4().bytes
                          for _i in range(0, constants.FRAME_MAX_SIZE)])
        await self.connect()
        await self.client.publish(self.exchange, self.routing_key, body)

    @testing.async_test
    async def test_publish_with_bad_exchange(self):

        def on_channel_close(reply_code, reply_text):
            self.assertEqual(reply_code, 404)
            self.assertTrue(reply_text.startswith('NOT_FOUND - no exchange'))
            self.test_finished.set()

        self.exchange = str(uuid.uuid4())
        self.client.register_channel_close_callback(on_channel_close)
        await self.connect()
        channel = self.client._channel
        await self.client.publish(self.exchange, self.routing_key, self.body)
        await self.test_finished.wait()
        await self.client._wait_on_state(client.STATE_CHANNEL_OPENOK_RECEIVED)

        self.assertEqual(self.client._channel, channel + 1)

    @testing.async_test
    async def test_publish_with_bad_exchange_and_mandatory(self):
        def on_message_return(msg):
            self.assertEqual(msg.exchange, self.exchange)
            self.assertEqual(msg.routing_key, self.routing_key)
            self.assertEqual(msg.body, self.body)
            self.test_finished.set()

        self.client.register_message_return_callback(on_message_return)
        await self.connect()
        await self.client.publish(
            self.exchange, self.routing_key, self.body, mandatory=True)
        await self.test_finished.wait()

    @testing.async_test
    async def test_publish_with_confirmation(self):
        await self.connect()
        await self.client.confirm_select()
        result = await self.client.publish(
            self.exchange, self.routing_key, self.body)
        self.assertTrue(result)
