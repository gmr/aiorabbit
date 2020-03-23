from aiorabbit import exceptions
from . import testing


class QueueTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_queue(self):
        queue = self.uuid4()
        exchange = 'amq.direct'
        routing_key = '#'
        await self.connect()
        msg_count, consumer_count = await self.client.queue_declare(queue)
        self.assertEqual(msg_count, 0)
        self.assertEqual(consumer_count, 0)
        await self.client.queue_bind(queue, exchange, routing_key)
        purged = await self.client.queue_purge(queue)
        self.assertEqual(purged, 0)
        await self.client.queue_unbind(queue, exchange, routing_key)
        await self.client.queue_delete(queue)

    @testing.async_test
    async def test_queue_bind_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.queue_bind(1)
        with self.assertRaises(TypeError):
            await self.client.queue_bind('foo', 1)
        with self.assertRaises(TypeError):
            await self.client.queue_bind('foo', 'bar', 1)
        with self.assertRaises(TypeError):
            await self.client.queue_bind('foo', 'bar', 'baz', 1)

    @testing.async_test
    async def test_queue_bind_missing_exchange(self):
        queue = self.uuid4()
        exchange = self.uuid4()
        routing_key = '#'
        await self.connect()
        await self.client.queue_declare(queue)
        with self.assertRaises(exceptions.NotFound):
            await self.client.queue_bind(queue, exchange, routing_key)
        await self.client.queue_delete(queue)

    @testing.async_test
    async def test_queue_declare(self):
        queue = self.uuid4()
        await self.connect()
        msg_count, consumer_count = await self.client.queue_declare(queue)
        self.assertEqual(msg_count, 0)
        self.assertEqual(consumer_count, 0)
        msg_count, consumer_count = await self.client.queue_declare(
            queue, passive=True)
        self.assertEqual(msg_count, 0)
        self.assertEqual(consumer_count, 0)
        with self.assertRaises(exceptions.ResourceLocked):
            await self.client.queue_declare(
                queue, exclusive=True, auto_delete=True)
        with self.assertRaises(exceptions.PreconditionFailed):
            await self.client.queue_declare(
                queue, auto_delete=True)
        await self.client.queue_delete(queue)

    @testing.async_test
    async def test_queue_declare_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.queue_declare(1)
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), 1)
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), passive='1')
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), durable='1')
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), exclusive='1')
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), auto_delete='1')
        with self.assertRaises(TypeError):
            await self.client.queue_declare(self.uuid4(), arguments='1')

    @testing.async_test
    async def test_queue_delete_not_found(self):
        await self.connect()
        await self.client.queue_delete(self.uuid4())

    @testing.async_test
    async def test_queue_delete_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.queue_delete(1)
        with self.assertRaises(TypeError):
            await self.client.queue_delete('foo', 1)
        with self.assertRaises(TypeError):
            await self.client.queue_delete('foo', False, 1)

    @testing.async_test
    async def test_queue_purge_not_found(self):
        await self.connect()
        with self.assertRaises(exceptions.NotFound):
            await self.client.queue_purge(self.uuid4())

    @testing.async_test
    async def test_queue_purge_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.queue_purge(1)

    @testing.async_test
    async def test_queue_unbind_missing_exchange(self):
        queue = self.uuid4()
        exchange = self.uuid4()
        routing_key = '#'
        await self.connect()
        await self.client.queue_declare(queue)
        await self.client.queue_unbind(queue, exchange, routing_key)

    @testing.async_test
    async def test_queue_unbind_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.queue_unbind(1)
        with self.assertRaises(TypeError):
            await self.client.queue_unbind('foo', 1)
        with self.assertRaises(TypeError):
            await self.client.queue_unbind('foo', 'bar', 1)
        with self.assertRaises(TypeError):
            await self.client.queue_unbind('foo', 'bar', 'baz', 1)
