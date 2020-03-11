Context Manager
===============

:meth:`~aiorabbit.connect` is an asynchronous `context manager <https://docs.python.org/3/reference/datamodel.html#context-managers>`_
that returns a connected instance of the :class:`aiorabbit.client.Client` class.
When exiting the runtime context, the client connection is automatically closed.

.. autofunction:: aiorabbit.connect
