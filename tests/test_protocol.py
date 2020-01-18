import asyncio

from aiorabbit import protocol
from . import testing


class TestCase(testing.AsyncTestCase):

    @testing.async_test
    async def test_unmarshalling_exception(self):
        def callback(*args):
            pass
        obj = protocol.AMQP(callback, callback, callback)
        frame_data = (b'\x01\x00\x01\x00\x00\x00\x00\x00<\x00P\x00\x00\x00\x00'
                      b'\x00\x00\x00\x01\x00\xce')
        obj.data_received(frame_data)
        self.assertEqual(len(frame_data), len(obj.buffer))

    @testing.async_test
    async def test_split_frame(self):
        def callback(*args):
            self.assertEqual(args[1].name, 'Tx.Select')
        obj = protocol.AMQP(callback, callback, callback)
        frame_data = b'\x01\x00\x01\x00\x00\x00\x04\x00'
        obj.data_received(frame_data)
        self.assertEqual(len(frame_data), len(obj.buffer))
        frame_data = b'Z\x00\n\xce'
        obj.data_received(frame_data)
        self.assertEqual(len(obj.buffer), 0)

    @testing.async_test
    async def test_multiple_frame(self):
        calls = []

        async def _on_connected():
            pass

        async def _on_disconnected(_exc):
            pass

        async def _on_frame(channel, frame):
            calls.append((channel, frame))

        obj = protocol.AMQP(_on_connected, _on_disconnected, _on_frame)
        frame_data = b'\x01\x00\x01\x00\x00\x00\x04\x00Z\x00\n\xce'
        frame_data += b'\x01\x00\x01\x00\x00\x00\x04\x00Z\x00\n\xce'
        self.assertEqual(len(frame_data), 24)
        obj.data_received(frame_data)
        await asyncio.sleep(0.1)  # Let the loop process calls
        self.assertEqual(len(obj.buffer), 0)
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertEqual(call[0], 1)  # Channel
            self.assertEqual(call[1].name, 'Tx.Select')
