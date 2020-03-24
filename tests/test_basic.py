import uuid

from pamqp import body, commands, header

from aiorabbit import exceptions, message
from . import testing


class BasicAckTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_ack('foo')
        with self.assertRaises(TypeError):
            await self.client.basic_ack(1, 1)


class BasicCancelTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_cancel(1)


class BasicConsumeTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.queue = self.uuid4()
        self.exchange = 'amq.topic'
        self.routing_key = self.uuid4()
        self.body = uuid.uuid4().bytes

    async def on_message(self, msg):
        self.assertEqual(msg.exchange, self.exchange)
        self.assertEqual(msg.routing_key, self.routing_key)
        self.assertEqual(msg.body, self.body)
        await self.client.basic_ack(msg.delivery_tag)
        self.test_finished.set()

    @testing.async_test
    async def test_consume(self):
        await self.connect()
        await self.client.queue_declare(self.queue)
        await self.client.queue_bind(self.queue, self.exchange, '#')
        ctag = await self.client.basic_consume(
            self.queue, callback=self.on_message)
        await self.client.publish(self.exchange, self.routing_key, self.body)
        await self.test_finished.wait()
        await self.client.basic_cancel(ctag)

    @testing.async_test
    async def test_consume_large_message(self):
        self.body = '-'.join([
            self.uuid4() for _i in range(0, 100000)]).encode('utf-8')
        await self.connect()
        await self.client.queue_declare(self.queue)
        await self.client.queue_bind(self.queue, self.exchange, '#')
        ctag = await self.client.basic_consume(
            self.queue, callback=self.on_message)
        await self.client.publish(self.exchange, self.routing_key, self.body)
        await self.test_finished.wait()
        await self.client.basic_cancel(ctag)

    @testing.async_test
    async def test_consume_message_pending(self):
        await self.connect()
        await self.client.queue_declare(self.queue)
        await self.client.queue_bind(self.queue, self.exchange, '#')
        await self.client.publish(self.exchange, self.routing_key, self.body)
        ctag = await self.client.basic_consume(
            self.queue, callback=self.on_message)
        await self.test_finished.wait()
        await self.client.basic_cancel(ctag)

    @testing.async_test
    async def test_consume_sync_callback(self):

        def on_message(msg):
            self.assertEqual(msg.exchange, self.exchange)
            self.assertEqual(msg.routing_key, self.routing_key)
            self.assertEqual(msg.body, self.body)
            self.test_finished.set()

        await self.connect()
        await self.client.queue_declare(self.queue)
        await self.client.queue_bind(self.queue, self.exchange, '#')
        await self.client.publish(self.exchange, self.routing_key, self.body)
        ctag = await self.client.basic_consume(self.queue, callback=on_message)
        await self.test_finished.wait()
        await self.client.basic_cancel(ctag)

    @testing.async_test
    async def test_not_found(self):
        await self.connect()
        with self.assertRaises(exceptions.NotFound):
            await self.client.basic_consume('foo', callback=lambda x: x)

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_consume(1, callback=lambda x: x)
        with self.assertRaises(TypeError):
            await self.client.basic_consume('foo', 1, callback=lambda x: x)
        with self.assertRaises(TypeError):
            await self.client.basic_consume(
                'foo', False, 1, callback=lambda x: x)
        with self.assertRaises(TypeError):
            await self.client.basic_consume(
                'foo', False, False, 1, callback=lambda x: x)
        with self.assertRaises(TypeError):
            await self.client.basic_consume(
                'foo', False, False, False, 1, callback=lambda x: x)
        with self.assertRaises(TypeError):
            await self.client.basic_consume('foo', callback=True)
        with self.assertRaises(ValueError):
            await self.client.basic_consume('foo')
        with self.assertRaises(TypeError):
            await self.client.basic_consume(
                'foo', callback=lambda x: x, consumer_tag=1)


class BasicGetTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_get(self):
        queue = self.uuid4()
        exchange = 'amq.direct'
        routing_key = '#'
        msg_body = uuid.uuid4().bytes
        await self.connect()
        msg_count, consumer_count = await self.client.queue_declare(queue)
        self.assertEqual(msg_count, 0)
        self.assertEqual(consumer_count, 0)
        result = await self.client.basic_get(queue)
        self.assertIsNone(result)
        await self.client.queue_bind(queue, exchange, routing_key)
        await self.client.publish(exchange, routing_key, msg_body)
        result = await self.client.basic_get(queue)
        self.assertIsInstance(result, message.Message)
        self.assertEqual(result.body, msg_body)
        self.assertEqual(result.message_count, 0)
        await self.client.basic_ack(result.delivery_tag)
        await self.client.queue_delete(queue)

    @testing.async_test
    async def test_basic_getok_message_count(self):
        queue = self.uuid4()
        exchange = 'amq.direct'
        routing_key = '#'
        msg_body = uuid.uuid4().bytes
        await self.connect()
        await self.client.queue_declare(queue)

        result = await self.client.basic_get(queue)
        self.assertIsNone(result)
        await self.client.queue_bind(queue, exchange, routing_key)
        await self.client.publish(exchange, routing_key, msg_body)
        await self.client.publish(exchange, routing_key, uuid.uuid4().bytes)
        await self.client.publish(exchange, routing_key, uuid.uuid4().bytes)

        result = await self.client.basic_get(queue)
        self.assertIsInstance(result, message.Message)
        self.assertEqual(result.body, msg_body)
        self.assertEqual(result.message_count, 2)
        await self.client.basic_ack(result.delivery_tag)

        result = await self.client.basic_get(queue)
        self.assertIsInstance(result, message.Message)
        self.assertEqual(result.message_count, 1)
        await self.client.basic_nack(result.delivery_tag, requeue=False)

        result = await self.client.basic_get(queue)
        self.assertIsInstance(result, message.Message)
        self.assertEqual(result.message_count, 0)
        await self.client.basic_reject(result.delivery_tag)

        await self.client.queue_delete(queue)

    @testing.async_test
    async def test_basic_get_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_get(1)
        with self.assertRaises(TypeError):
            await self.client.basic_get('foo', 1)


class BasicNackTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_nack('foo')
        with self.assertRaises(TypeError):
            await self.client.basic_nack(1, 1)
        with self.assertRaises(TypeError):
            await self.client.basic_nack(1, False, 1)


class BasicPublishTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_publish_raises(self):
        with self.assertRaises(NotImplementedError):
            await self.client.basic_publish()


class BasicQosTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_qos_raises(self):
        self.raises = self.assertRaises(NotImplementedError)
        with self.raises:
            await self.client.basic_qos()


class BasicRecoverTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_basic_recover(self):
        await self.connect()
        await self.client.basic_recover(True)

    @testing.async_test
    async def test_basic_recover_false_raises(self):
        await self.connect()
        with self.assertRaises(exceptions.NotImplemented):
            await self.client.basic_recover(False)

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_recover(1)


class BasicRejectTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.basic_reject('foo')
        with self.assertRaises(TypeError):
            await self.client.basic_reject(1, 1)


class BasicReturnTestCase(testing.ClientTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.exchange = 'amq.topic'
        self.routing_key = self.uuid4()
        self.body = uuid.uuid4().bytes

    @testing.async_test
    async def test_basic_return(self):

        async def on_return(msg: message.Message) -> None:
            self.assertEqual(msg.reply_code, 404)
            self.assertEqual(msg.reply_text, 'Not Found')
            self.assertEqual(msg.exchange, self.exchange)
            self.assertEqual(msg.body, self.body)
            self.test_finished.set()

        self.client.register_basic_return_callback(on_return)

        await self.connect()
        await self.client.publish(self.exchange, self.routing_key, self.body)

        # Fake the Basic.Return
        self.client._on_frame(self.client._channel, commands.Basic.Return(
            404, 'Not Found', self.exchange, self.routing_key))
        self.client._on_frame(self.client._channel, header.ContentHeader(
            0, len(self.body), commands.Basic.Properties()))
        self.client._on_frame(
            self.client._channel, body.ContentBody(self.body))

        await self.test_finished.wait()
