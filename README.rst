aiorabbit
=========
aiorabbit is an opinionated AsyncIO RabbitMQ client for `Python 3 <https://www.python.org/>`_ (3.7+).

|Version| |Status| |Coverage| |License|

Project Goals
-------------
- To create a simple, robust `RabbitMQ <https://rabbitmq.com>`_ client library for `AsyncIO <https://docs.python.org/3/library/asyncio.html>`_ development in Python 3.
- To make use of new features and capabilities in Python 3.7+.
- Remove some complexity in using an `AMQP <https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol>`_ client by:
   - Abstracting away the AMQP channel and use it only as a protocol coordination mechanism inside the client.
   - Remove the `nowait <https://www.rabbitmq.com/amqp-0-9-1-reference.html#domain.no-wait>`_ keyword to ensure a single round-trip pattern of behavior for client usage.
- To automatically reconnect when a connection is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To automatically create a new channel when the channel is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To ensure correctness of API usage, including values passed to RabbitMQ in AMQ method calls.

Example Use
-----------
The following demonstrates an example of using the library to publish a message with publisher confirmations enabled:

.. code-block:: python

    import asyncio
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
        asyncio.get_event_loop().run_until_complete(main())

Documentation
-------------
http://aiorabbit.readthedocs.org

License
-------
Copyright (c) 2019-2020 Gavin M. Roy
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of the copyright holder nor the names of its contributors may
  be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
