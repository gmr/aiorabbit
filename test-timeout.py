import asyncio
import datetime
import logging
import os
import ssl
import time
import uuid

import aiorabbit

LOGGER = logging.getLogger(__name__)


async def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(
        '/Users/gavinr/Desktop/AWeber/acm-pca-cacert.pem')
    async with aiorabbit.connect(os.environ.get('RABBITMQ_URL', ''),
                                 ssl_context=context) as client:
        while True:
            count = 0
            while count < 25:
                LOGGER.info('Sleeping for 60 seconds')
                time.sleep(30)
                count += 1

            LOGGER.info('Publishing')
            await client.publish(
                'amq.direct',
                'routing-key',
                b'message body',
                app_id='example',
                message_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.utcnow())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.get_event_loop().run_until_complete(main())
