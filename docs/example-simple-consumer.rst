Async Generator Consumer
========================

The following example implements a simple consumer using the async generator
based :meth:`aiorabbit.client.Client.consume` method. It performs similar
high-level logic to the :doc:`example-callback-consumer`:

1. Connect to RabbitMQ
2. Ensures the queue to consume from exists
3. Starts the consumer
4. As each message is received:
    - If the message body is ``stop``, break out of the consumer
    - or ack with a 75% chance
    - or nack without requeue
5. Stop consuming and close the connection

.. note:: Specify the RabbitMQ URL to connect to in the ``RABBITMQ_URL`` environment
          variable prior to running this example.

.. code-block:: python3
   :caption: simple-consumer.py

    import asyncio
    import logging
    import os
    import random

    import aiorabbit

    LOGGER = logging.getLogger(__name__)


    async def main():
        queue_name = 'test-queue'
        async with aiorabbit.connect(os.environ.get('RABBITMQ_URL', '')) as client:
            await client.queue_declare(queue_name)
            LOGGER.info('Consuming from %s', queue_name)
            async for msg in client.consume(queue_name):
                LOGGER.info('Received message published to %s: %r',
                            queue_name, msg.body)
                if msg.body == b'stop':
                    await client.basic_ack(msg.delivery_tag)
                    break
                elif random.randint(1, 100) <= 75:
                    await client.basic_ack(msg.delivery_tag)
                else:
                    await client.basic_nack(msg.delivery_tag, requeue=False)
        LOGGER.info('Stopped consuming')

    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        asyncio.get_event_loop().run_until_complete(main())


Run the code, open the RabbitMQ management UI in your browser, and publish a
few messages to the queue. When you've sent enough, publish a message with the
body of ``stop``. You should see output similar to the following:

.. code-block::

    $ python3 simple-consumer.py
    INFO:aiorabbit.client:Connecting to amqp://guest:*****@localhost:32773/%2F
    INFO:__main__:Consuming from test-queue
    INFO:__main__:Received message published to test-queue: b'Simple Example Message 1'
    INFO:__main__:Received message published to test-queue: b'Simple Example Message 2'
    INFO:__main__:Received message published to test-queue: b'stop'
    INFO:__main__:Stopped consuming
