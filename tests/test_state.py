import asyncio
import typing
import unittest

from aiorabbit import exceptions, state


class Test(state.StateManager):

    STATE_UNINITIALIZED: typing.Final[int] = 0x00
    STATE_FOO: typing.Final[int] = 0x01
    STATE_BAR: typing.Final[int] = 0x02
    STATE_BAZ: typing.Final[int] = 0x03

    STATE_MAP: typing.Final[dict] = {
        STATE_UNINITIALIZED: 'Uninitialized',
        STATE_FOO: 'Foo',
        STATE_BAR: 'Bar',
        STATE_BAZ: 'Baz',

    }
    STATE_TRANSITIONS: dict = {
        STATE_UNINITIALIZED: {STATE_FOO, STATE_BAR},
        STATE_FOO: {STATE_BAR},
        STATE_BAR: {STATE_BAZ},
        STATE_BAZ: {STATE_FOO}
    }

    def set_state(self, value: int) -> None:
        self._set_state(value)


class TestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.obj = Test(self.loop)

    def assert_state(self, value):
        self.assertEqual(self.obj.state, self.obj.STATE_MAP[value])

    def test_state_transitions(self):
        self.assert_state(self.obj.STATE_UNINITIALIZED)
        self.obj.set_state(self.obj.STATE_FOO)
        self.assert_state(self.obj.STATE_FOO)
        self.obj.set_state(self.obj.STATE_BAR)
        self.assert_state(self.obj.STATE_BAR)
        self.obj.set_state(self.obj.STATE_BAZ)
        self.assert_state(self.obj.STATE_BAZ)
        self.obj.set_state(self.obj.STATE_FOO)
        self.assert_state(self.obj.STATE_FOO)

    def test_invalid_state_transition(self):
        self.assert_state(self.obj.STATE_UNINITIALIZED)
        with self.assertRaises(exceptions.StateTransitionError):
            self.obj.set_state(self.obj.STATE_BAZ)

    def test_setting_state_to_same_value(self):
        self.assert_state(self.obj.STATE_UNINITIALIZED)
        self.obj.set_state(self.obj.STATE_FOO)
        state_start = self.obj._state_start
        self.assert_state(self.obj.STATE_FOO)
        self.obj.set_state(self.obj.STATE_FOO)
        self.assertNotEqual(state_start, self.obj._state_start)

    def test_wait_on_state(self):

        async def run_test():
            self.loop.call_soon(self.obj.set_state, self.obj.STATE_FOO)
            await self.obj._wait_on_state(self.obj.STATE_FOO)
            self.loop.call_soon(self.obj.set_state, self.obj.STATE_BAR)
            await self.obj._wait_on_state(self.obj.STATE_BAR)

        self.loop.run_until_complete(asyncio.ensure_future(run_test()))
        self.assert_state(self.obj.STATE_BAR)
