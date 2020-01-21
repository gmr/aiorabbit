# coding=utf-8
import uuid

from . import testing


class ExchangeDeclareTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_exchange_declare(self):
        name = str(uuid.uuid4().hex)
        await self.connect()
        await self.client.exchange_declare(name, 'direct', durable=True)
        self.assertTrue(
            await self.client.exchange_declare(name, 'direct', passive=True))

    @testing.async_test
    async def test_exchange_declare_passive_fails(self):
        await self.connect()
        self.assertFalse(
            await self.client.exchange_declare(
                str(uuid.uuid4().hex), 'direct', passive=True))
