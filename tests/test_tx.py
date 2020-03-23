from aiorabbit import exceptions
from . import testing


class TransactionTestCase(testing.ClientTestCase):

    @testing.async_test
    async def test_commit_and_rollback(self):
        await self.connect()
        await self.client.tx_select()
        await self.client.tx_rollback()
        await self.client.tx_commit()

    @testing.async_test
    async def test_double_select(self):
        await self.connect()
        await self.client.tx_select()
        await self.client.tx_select()

    @testing.async_test
    async def test_commit_without_select(self):
        await self.connect()
        with self.assertRaises(exceptions.NoTransactionError):
            await self.client.tx_commit()

    @testing.async_test
    async def test_rollback_without_select(self):
        await self.connect()
        with self.assertRaises(exceptions.NoTransactionError):
            await self.client.tx_rollback()
