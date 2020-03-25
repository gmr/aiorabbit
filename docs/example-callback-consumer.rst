Callback-Based Consumer
=======================

The following example implements a callback-based consumer. This style of consumer
could be useful as part of a larger application, where consuming is only one part
of the main application flow.  It performs similar high-level logic to the
:doc:`example-simple-consumer`.

.. code-block:: python3
   :caption: callback-consumer.py

    import asyncio
    import logging
    import os
    import random

    from aiorabbit import client, exceptions, message

    LOGGER = logging.getLogger(__name__)


    class Consumer:
        """Class that demonstrates a consumer application lifecycle"""

        def __init__(self, rabbitmq_url: str, queue_name: str):
            self.client = client.Client(rabbitmq_url)
            self.queue_name = queue_name
            self.shutdown = asyncio.Event()

        async def execute(self) -> None:
            """Performs the following steps:

            1. Connects to RabbitMQ and exits on authentication failure
            2. Ensures the queue to consume from exists
            3. Starts the consumer
            4. Blocks until ``self.shutdown`` is set
            5. Stops consuming
            6. Closes the connection

            """
            try:
                await self.client.connect()
            except exceptions.AccessRefused as err:
                LOGGER.error('Failed to authenticate to RabbitMQ: %s', err)
                return

            await self.client.queue_declare(self.queue_name)

            consumer_tag = await self.client.basic_consume(
                self.queue_name, callback=self.on_message)
            LOGGER.info('Started consuming on queue %s with consumer tag %s',
                        self.queue_name, consumer_tag)

            await self.shutdown.wait()
            LOGGER.info('Shutting down')

            await self.client.basic_cancel(consumer_tag)
            await self.client.close()

        async def on_message(self, msg: message.Message) -> None:
            """Receives the message from RabbitMQ and...

            - If the message body is ``stop``, ack it and set shutdown event
            - or ack with a 75% chance
            - or nack without requeue

            """
            LOGGER.info('Received message published to %s: %r',
                        self.queue_name, msg.body)
            if msg.body == b'stop':
                await self.client.basic_ack(msg.delivery_tag)
                self.shutdown.set()
            elif random.randint(1, 100) <= 75:
                await self.client.basic_ack(msg.delivery_tag)
            else:
                await self.client.basic_nack(msg.delivery_tag, requeue=False)


    async def main():
        await Consumer(os.environ.get('RABBITMQ_URL', ''), 'test-queue').execute()


    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        asyncio.get_event_loop().run_until_complete(main())

Run the code, open the RabbitMQ management UI in your browser, and publish a
few messages to the queue. When you've sent enough, publish a message with the
body of ``stop``. You should see output similar to the following:

.. code-block::

    $ python3 callback-consumer.py
    INFO:aiorabbit.client:Connecting to amqp://guest:*****@localhost:32773/%2F
    INFO:__main__:Started consuming on queue test-queue with consumer tag amq.ctag-4DSHNNZGxrf22bxS_i0uqA
    INFO:__main__:Received message published to test-queue: b'example #1'
    INFO:__main__:Received message published to test-queue: b'example #2'
    INFO:__main__:Received message published to test-queue: b'stop'
    INFO:__main__:Shutting down
