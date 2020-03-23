# coding=utf-8
import uuid

from aiorabbit import exceptions
from . import testing


class ExchangeDeclareTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_exchange_declare(self):
        name = str(uuid.uuid4().hex)
        await self.connect()
        await self.client.exchange_declare(name, 'direct', durable=True)
        await self.client.exchange_declare(name, 'direct', passive=True)

    @testing.async_test
    async def test_exchange_declare_passive_raises(self):
        await self.connect()
        with self.assertRaises(exceptions.NotFound):
            await self.client.exchange_declare(
                str(uuid.uuid4().hex), 'direct', passive=True)


class ExchangeTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_exchange_declare(self):
        await self.connect()
        await self.client.exchange_declare(self.uuid4(), 'direct')

    @testing.async_test
    async def test_exchange_declare_invalid_exchange_type(self):
        await self.connect()
        with self.assertRaises(exceptions.CommandInvalid):
            await self.client.exchange_declare(self.uuid4(), self.uuid4())
        self.assertEqual(self.client.state, 'Channel Open')
        # Ensure a command will properly work after the error
        await self.client.exchange_declare(self.uuid4(), 'direct')

    @testing.async_test
    async def test_exchange_declare_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(1)
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), 1)
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), passive='1')
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), durable='1')
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), auto_delete='1')
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), internal='1')
        with self.assertRaises(TypeError):
            await self.client.exchange_declare(self.uuid4(), arguments='1')

    @testing.async_test
    async def test_exchange_bind_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.exchange_bind(1, self.uuid4(), self.uuid4())
        with self.assertRaises(TypeError):
            await self.client.exchange_bind(self.uuid4(), 1, self.uuid4())
        with self.assertRaises(TypeError):
            await self.client.exchange_bind(self.uuid4(), self.uuid4(), 1)
        with self.assertRaises(TypeError):
            await self.client.exchange_bind(
                self.uuid4(), self.uuid4(), self.uuid4(), self.uuid4())

    @testing.async_test
    async def test_exchange_bind_raises_exchange_not_found(self):
        await self.connect()
        self.assertEqual(self.client._channel, 1)
        with self.assertRaises(exceptions.NotFound):
            await self.client.exchange_bind(
                self.uuid4(), self.uuid4(), self.uuid4())
        self.assertEqual(self.client._channel, 2)
        # Ensure a command will properly work after the error
        await self.client.exchange_declare(self.uuid4(), 'direct')

    @testing.async_test
    async def test_exchange_bind(self):
        await self.connect()
        exchange_1 = self.uuid4()
        exchange_2 = self.uuid4()
        await self.client.exchange_declare(exchange_1, 'topic')
        await self.client.exchange_declare(exchange_2, 'topic')
        await self.client.exchange_bind(exchange_1, exchange_2, '#')
        await self.client.exchange_unbind(exchange_1, exchange_2, '#')
        await self.client.exchange_delete(exchange_2)
        await self.client.exchange_delete(exchange_1)

    @testing.async_test
    async def test_exchange_delete_invalid_exchange_name(self):
        await self.connect()
        self.assertEqual(self.client._channel, 1)
        with self.assertRaises(TypeError):
            await self.client.exchange_delete(327687)

    @testing.async_test
    async def test_exchange_unbind_validation_errors(self):
        await self.connect()
        with self.assertRaises(TypeError):
            await self.client.exchange_unbind(1, self.uuid4(), self.uuid4())
        with self.assertRaises(TypeError):
            await self.client.exchange_unbind(self.uuid4(), 1, self.uuid4())
        with self.assertRaises(TypeError):
            await self.client.exchange_unbind(self.uuid4(), self.uuid4(), 1)
        with self.assertRaises(TypeError):
            await self.client.exchange_unbind(
                self.uuid4(), self.uuid4(), self.uuid4(), self.uuid4())

    @testing.async_test
    async def test_exchange_unbind_invalid_exchange(self):
        await self.connect()
        self.assertEqual(self.client._channel, 1)
        await self.client.exchange_unbind(
            self.uuid4(), self.uuid4(), self.uuid4())
        self.assertEqual(self.client._channel, 1)
