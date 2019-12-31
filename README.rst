aiorabbit
=========
aiorabbit is an AsyncIO RabbitMQ client for Python 3.

|Version| |Status| |Coverage| |License|

Project Goals
-------------
- To create a simple, robust RabbitMQ client library for AsyncIO development in Python 3
- To make use of new features and capabilities in Python 3.7+
- To abstract away the AMQP channel and use it only as a protocol coordination mechanism inside the client
- To provide built-in support for multiple brokers and automatic reconnection

Example Use
-----------
The following demonstrates an example of the intended behavior for the library:

.. code-block:: python

    import time
    import uuid

    import aiorabbit

    RABBITMQ_URL = 'amqps://guest:guest@localhost:5672/%2f'


    async def main():
        client = await aiorabbit.connect(RABBITMQ_URL)
        await client.confirm_select()

        response = await client.publish(
            'exchange', 'routing-key', 'message-body', app_id='example',
            message_id=str(uuid.uuid4()), timestamp=int(time.time()),
            mandatory=True)

        if not response.ok:
            print('Publishing failure: {!r} {!r}'.format(
                response.error, response.message))

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
