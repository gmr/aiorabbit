from aiorabbit import exceptions, state
from . import testing

STATE_FOO = 0x10
STATE_BAR = 0x11
STATE_BAZ = 0x12


class State(state.StateManager):

    STATE_MAP = {
        state.STATE_UNINITIALIZED: 'Uninitialized',
        state.STATE_EXCEPTION: 'Exception',
        STATE_FOO: 'Foo',
        STATE_BAR: 'Bar',
        STATE_BAZ: 'Baz',

    }
    STATE_TRANSITIONS = {
        state.STATE_UNINITIALIZED: [STATE_FOO, STATE_BAR],
        state.STATE_EXCEPTION: [],
        STATE_FOO: [STATE_BAR],
        STATE_BAR: [STATE_BAZ],
        STATE_BAZ: [STATE_FOO]
    }

    def set_state(self, value: int) -> None:
        self._set_state(value)

    def set_exception(self, exc):
        self._set_state(state.STATE_EXCEPTION, exc)


class TestCase(testing.AsyncTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.obj = State(self.loop)

    def assert_state(self, value):
        self.assertEqual(self.obj.state, self.obj.STATE_MAP[value])

    def test_state_transitions(self):
        self.assert_state(state.STATE_UNINITIALIZED)
        self.obj.set_state(STATE_FOO)
        self.assert_state(STATE_FOO)
        self.obj.set_state(STATE_BAR)
        self.assert_state(STATE_BAR)
        self.obj.set_state(STATE_BAZ)
        self.assert_state(STATE_BAZ)
        self.obj.set_state(STATE_FOO)
        self.assert_state(STATE_FOO)

    def test_invalid_state_transition(self):
        self.assert_state(state.STATE_UNINITIALIZED)
        with self.assertRaises(exceptions.StateTransitionError):
            self.obj.set_state(STATE_BAZ)
        self.assertIsInstance(self.obj._exception,
                              exceptions.StateTransitionError)

    def test_setting_state_to_same_value(self):
        self.assert_state(state.STATE_UNINITIALIZED)
        self.obj.set_state(STATE_FOO)
        self.assert_state(STATE_FOO)
        self.obj.set_state(STATE_FOO)

    @testing.async_test
    async def test_wait_on_state(self):
        self.loop.call_soon(self.obj.set_state, STATE_FOO)
        await self.obj._wait_on_state(STATE_FOO)
        self.loop.call_soon(self.obj.set_state, STATE_BAR)
        await self.obj._wait_on_state(STATE_BAR)
        self.assert_state(STATE_BAR)

    @testing.async_test
    async def test_exception_while_waiting(self):
        self.loop.call_soon(self.obj.set_state, STATE_FOO)
        await self.obj._wait_on_state(STATE_FOO)
        self.loop.call_soon(self.obj.set_exception, RuntimeError)
        with self.assertRaises(RuntimeError):
            await self.obj._wait_on_state(STATE_BAR)
