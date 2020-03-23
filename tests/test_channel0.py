import asyncio
import logging
import platform
import typing
import unittest
from unittest import mock
import uuid

from pamqp import commands, constants, frame, heartbeat
from pamqp import exceptions as pamqp_exceptions

from aiorabbit import channel0, exceptions, state, version

LOGGER = logging.getLogger(__name__)


class TestCase(unittest.TestCase):

    HEARTBEAT_INTERVAL = 10
    SERVER_HEARTBEAT_INTERVAL = 30
    MAX_CHANNELS = 256
    SERVER_MAX_CHANNELS = 32768

    def setUp(self):
        self.blocked = asyncio.Event()
        self.username = str(uuid.uuid4())
        self.password = str(uuid.uuid4())
        self.locale = str(uuid.uuid4())
        self.product = str(uuid.uuid4())
        self.virtual_host = '/'
        self.heartbeat = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        self.on_remote_close = mock.Mock()
        self.server_properties = {
            'capabilities': {'authentication_failure_close': True,
                             'basic.nack': True,
                             'connection.blocked': True,
                             'consumer_cancel_notify': True,
                             'consumer_priorities': True,
                             'direct_reply_to': True,
                             'per_consumer_qos': True,
                             'publisher_confirms': True},
            'cluster_name': 'mock@{}'.format(str(uuid.uuid4())),
            'platform': 'Python {}'.format(platform.python_version()),
            'production': 'aiorabbit',
            'version': version
        }
        self.transport = mock.create_autospec(asyncio.Transport)
        self.transport.write = self._transport_write
        self.channel0 = channel0.Channel0(
            self.blocked,
            self.username,
            self.password,
            self.virtual_host,
            self.HEARTBEAT_INTERVAL,
            self.locale,
            self.loop,
            self.MAX_CHANNELS,
            self.product,
            self.on_remote_close)

    def _connection_start(self):
        self.channel0.process(
            commands.Connection.Start(
                server_properties=self.server_properties))

    def _connection_tune(self):
        self.channel0.process(
            commands.Connection.Tune(
                self.SERVER_MAX_CHANNELS, constants.FRAME_MAX_SIZE,
                self.SERVER_HEARTBEAT_INTERVAL))

    def _connection_open_ok(self):
        self.channel0.process(commands.Connection.OpenOk())

    def _connection_close_ok(self):
        self.channel0.process(commands.Connection.CloseOk())

    def _transport_write(self, value: bytes) -> typing.NoReturn:
        count, channel, frame_value = frame.unmarshal(value)
        self.assertEqual(count, len(value), 'All bytes used')
        self.assertEqual(channel, 0, 'Frame was published on channel 0')
        if frame_value.name == 'ProtocolHeader':
            self.loop.call_soon(self._connection_start)
        elif frame_value.name == 'Connection.StartOk':
            self.loop.call_soon(self._connection_tune)
        elif frame_value.name == 'Connection.TuneOk':
            pass
        elif frame_value.name == 'Connection.Open':
            self.loop.call_soon(self._connection_open_ok)
        elif frame_value.name == 'Connection.Close':
            self.loop.call_soon(self._connection_close_ok)
        elif frame_value.name == 'Connection.CloseOk':
            pass
        elif frame_value.name == 'Heartbeat':
            self.heartbeat.set()
        else:
            raise RuntimeError(count, channel, frame_value)

    async def open(self):
        self.assert_state(state.STATE_UNINITIALIZED)
        await self.channel0.open(self.transport)

    def assert_state(self, value):
        self.assertEqual(
            self.channel0.state_description(value), self.channel0.state)

    def test_negotiation(self):
        self.loop.run_until_complete(self.open())


class ProtocolMismatchTestCase(TestCase):

    def _connection_start(self):
        self.channel0.process(
            commands.Connection.Start(
                version_major=1, version_minor=0,
                server_properties=self.server_properties))

    def test_negotiation(self):
        with self.assertRaises(exceptions.ClientNegotiationException):
            self.loop.run_until_complete(self.open())
        self.assert_state(state.STATE_EXCEPTION)


class RemoteCloseTestCase(TestCase):

    def test_with_remote_200(self):
        self.loop.run_until_complete(self.open())
        self.channel0.process(commands.Connection.Close(200, 'OK'))
        self.assert_state(channel0.STATE_CLOSE_OK_SENT)

    def test_with_fake_code(self):
        self.loop.run_until_complete(self.open())
        with self.assertRaises(exceptions.ConnectionClosedException):
            self.channel0.process(
                commands.Connection.Close(999, 'Error'))
        self.assert_state(state.STATE_EXCEPTION)

    def test_with_invalid_path(self):
        self.loop.run_until_complete(self.open())
        with self.assertRaises(pamqp_exceptions.AMQPInvalidPath):
            self.channel0.process(
                commands.Connection.Close(402, 'INVALID-PATH'))
        self.assert_state(state.STATE_EXCEPTION)


class ClientCloseTestCase(TestCase):

    def test_close(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.loop.run_until_complete(self.channel0.close())
        self.assert_state(channel0.STATE_CLOSED)


class ConnectionBlockedTestCase(TestCase):

    def test_block_unblock(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.channel0.process(commands.Connection.Blocked())
        self.assert_state(channel0.STATE_BLOCKED_RECEIVED)
        self.assertTrue(self.channel0.blocked.is_set())
        self.channel0.process(commands.Connection.Unblocked())
        self.assert_state(channel0.STATE_UNBLOCKED_RECEIVED)
        self.assertFalse(self.channel0.blocked.is_set())


class HeartbeatTestCase(TestCase):

    def test_heartbeat(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.channel0.process(heartbeat.Heartbeat())
        self.assert_state(channel0.STATE_HEARTBEAT_SENT)
        self.assertTrue(self.heartbeat.is_set())


class NoHeartbeatTestCase(TestCase):

    HEARTBEAT_INTERVAL = 0
    SERVER_HEARTBEAT_INTERVAL = 0

    def test_negotiated_interval(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.assertEqual(self.channel0.heartbeat_interval, 0)


class NoClientHeartbeatTestCase(TestCase):

    HEARTBEAT_INTERVAL = None
    SERVER_HEARTBEAT_INTERVAL = 0

    def test_negotiated_interval(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.assertEqual(self.channel0.heartbeat_interval, 0)


class SmallerClientHeartbeatTestCase(TestCase):

    HEARTBEAT_INTERVAL = 10
    SERVER_HEARTBEAT_INTERVAL = 30

    def test_negotiated_interval(self):
        self.loop.run_until_complete(self.open())
        self.assert_state(channel0.STATE_OPEN_OK_RECEIVED)
        self.assertEqual(self.channel0.heartbeat_interval, 10)


class InvalidFrameTestCase(TestCase):

    def test_invalid_frame_raises(self):
        with self.assertRaises(exceptions.AIORabbitException):
            self.channel0.process(commands.Basic.Cancel('foo'))


class ResetTestCase(TestCase):

    def test_reset_attributes(self):
        self.loop.run_until_complete(self.open())
        self.assertDictEqual(self.channel0.properties, self.server_properties)
        self.channel0.reset()
        self.assertDictEqual(self.channel0.properties, {})
