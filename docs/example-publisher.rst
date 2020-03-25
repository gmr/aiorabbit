Message Publisher
=================

This example publisher demonstrates the usage of the Async Context Manager function
:func:`aiorabbit.connect`. It enables `Publisher Confirms <https://www.rabbitmq.com/confirms.html>`_
and then publishes a message.

.. note:: Specify the RabbitMQ URL to connect to in the ``RABBITMQ_URL`` environment
          variable prior to running this example.

.. code-block:: python3
   :caption: publisher-example.py

    import asyncio
    import datetime
    import logging
    import os
    import uuid

    import aiorabbit

    LOGGER = logging.getLogger(__name__)


    async def main():
        async with aiorabbit.connect(os.environ.get('RABBITMQ_URL', '')) as client:
            await client.confirm_select()
            if not await client.publish(
                    'amq.direct',
                    'routing-key',
                    b'message body',
                    app_id='example',
                    message_id=str(uuid.uuid4()),
                    timestamp=datetime.datetime.utcnow()):
                LOGGER.error('Publishing failure')
            else:
                LOGGER.info('Message published')


    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        asyncio.get_event_loop().run_until_complete(main())


If you do not alter the code, when you run it, you should see output similar to the following:

.. code-block::

    $ python3 publisher-example.py
    INFO:aiorabbit.client:Connecting to amqp://guest:*****@localhost:32773/%2F
    INFO:__main__:Message published

.. warning::

    RabbitMQ will only indicate a publishing failure via publisher confirms
    when there is an internal error in RabbitMQ. They are not a mechanism for
    guaranteeing a message is routed. Usage of the ``mandatory`` flag when
    publishing will guarantee that the message is at least routed into a valid
    exchange, but not that they are routed into a queue. Not using the ``mandatory``
    flag will allow your messages to be published to a non-existent exchange.
