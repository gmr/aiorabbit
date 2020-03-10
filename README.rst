aiorabbit
=========
aiorabbit is an opinionated AsyncIO RabbitMQ client for Python 3.

|Version| |Status| |Coverage| |License|

Project Goals
-------------
- To create a simple, robust RabbitMQ client library for AsyncIO development in Python 3.
- To make use of new features and capabilities in Python 3.7+.
- Remove some complexity in using an AMQP client by:
   - Abstracting away the AMQP channel and use it only as a protocol coordination mechanism inside the client.
   - Remove the `nowait` keyword to ensure a single round-trip pattern of behavior for client usage.
- To automatically reconnect when a connection is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To automatically create a new channel when the channel is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To provide built-in support for multiple brokers.
- To ensure correctness of API usage, including values passed to RabbitMQ in AMQ method calls.

Example Use
-----------
The following demonstrates an example of using the library to publish a message with publisher confirmations enabled:

.. code-block:: python

    import datetime
    import uuid

    import aiorabbit

    RABBITMQ_URL = 'amqps://guest:guest@localhost:5672/%2f'


    async def main():
        async with aiorabbit.connect(RABBITMQ_URL) as client:
            await client.confirm_select()
            if not await client.publish(
                    'exchange',
                    'routing-key',
                    'message-body',
                    app_id='example',
                    message_id=str(uuid.uuid4()),
                    timestamp=datetime.datetime.utcnow()):
                print('Publishing failure')

    if __name__ == '__main__':
        asyncio.run(main())

Documentation
-------------
http://aiorabbit.readthedocs.org

License
-------
BSD

Python Versions Supported
-------------------------
3.7+

.. |Version| image:: https://img.shields.io/pypi/v/aiorabbit.svg?
   :target: https://pypi.python.org/pypi/aiorabbit

.. |Status| image:: https://github.com/gmr/aiorabbit/workflows/Testing/badge.svg?
   :target: https://github.com/gmr/aiorabbit/actions?workflow=Testing
   :alt: Build Status

.. |Coverage| image:: https://img.shields.io/codecov/c/github/gmr/aiorabbit.svg?
   :target: https://codecov.io/github/gmr/aiorabbit?branch=master

.. |License| image:: https://img.shields.io/pypi/l/aiorabbit.svg?
   :target: https://aiorabbit.readthedocs.org
