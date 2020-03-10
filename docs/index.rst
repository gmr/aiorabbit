aiorabbit
=========

aiorabbit is an opinionated :mod:`asyncio` `RabbitMQ <https://rabbitmq.com>`_ client for Python 3.

|Version| |License|

Project Goals
-------------
- To create a simple, robust `RabbitMQ <https://rabbitmq.com>`_ client library for :mod:`asyncio` development in Python 3.
- To make use of new features and capabilities in Python 3.7+.
- Remove some complexity in using an `AMQP <https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol>`_ client by:
   - Abstracting away the AMQP channel and use it only as a protocol coordination mechanism inside the client.
   - Remove the `nowait <https://www.rabbitmq.com/amqp-0-9-1-reference.html#domain.no-wait>`_ keyword to ensure a single round-trip pattern of behavior for client usage.
- To automatically reconnect when a connection is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To automatically create a new channel when the channel is closed due to an AMQP exception/error.

  *When such a behavior is encountered, the exception is raised, but the client continues to operate if the user catches and logs the error.*
- To ensure correctness of API usage, including values passed to RabbitMQ in AMQ method calls.

Installation
------------
aiorabbit is available via the `Python Package Index <https://pypi.org>`_.

.. code::

    pip3 install aiorabbit

Documentation
-------------

.. toctree::
   :maxdepth: 1

   goals
   usage
   api
   exceptions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |Version| image:: https://img.shields.io/pypi/v/aiorabbit.svg?
   :target: https://pypi.python.org/pypi/aiorabbit
   :alt: Package Version

.. |License| image:: https://img.shields.io/pypi/l/aiorabbit.svg?
   :target: https://github.com/gmr/aiorabbit/blob/master/LICENSE
   :alt: BSD
