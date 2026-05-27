import unittest

from aiorabbit import exceptions


class ClassMappingTestCase(unittest.TestCase):
    """Exercise the AMQP reply-code to exception class mapping."""

    def test_known_amqp_reply_code_maps_to_concrete_exception(self):
        self.assertIs(exceptions.CLASS_MAPPING[404], exceptions.NotFound)

    def test_heartbeat_timeout_maps_to_connection_closed(self):
        # Channel0._heartbeat_check synthesises reply code 599 when the broker
        # stops sending heartbeats. Client._on_remote_close translates that to
        # ConnectionClosedException directly, but the same code is later
        # re-translated by Client.publish and Client._post_wait_on_state via
        # CLASS_MAPPING. Without an explicit entry those sites fall back to
        # UnknownError, which loses the semantic that the connection has been
        # closed.
        self.assertIs(
            exceptions.CLASS_MAPPING[599],
            exceptions.ConnectionClosedException)

    def test_unmapped_reply_code_falls_back_to_unknown_error(self):
        self.assertIs(
            exceptions.CLASS_MAPPING.get(999, exceptions.UnknownError),
            exceptions.UnknownError)
