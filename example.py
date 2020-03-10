import asyncio
import os
import pprint

import aiorabbit

RABBITMQ_URL = 'amqps://guest:guest@localhost:5672/%2f'


async def main():
    async with aiorabbit.connect(os.environ['RABBITMQ_URI']) as client:
        pprint.pprint(client.server_properties)

asyncio.get_event_loop().run_until_complete(main())
