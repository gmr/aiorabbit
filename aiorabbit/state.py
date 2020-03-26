# coding: utf-8
import asyncio
import inspect
import logging
import time
import typing

from aiorabbit import exceptions

STATE_UNINITIALIZED = 0x00
STATE_EXCEPTION = 0x01


class StateManager:
    """Base Class used to implement state management"""
    STATE_MAP: dict = {
        STATE_UNINITIALIZED: 'Uninitialized',
        STATE_EXCEPTION: 'Exception Raised'
    }

    STATE_TRANSITIONS: dict = {
        STATE_UNINITIALIZED: [STATE_EXCEPTION]
    }

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._logger = logging.getLogger(
            dict(inspect.getmembers(self))['__module__'])
        self._exception: typing.Optional[Exception] = None
        self._loop: asyncio.AbstractEventLoop = loop
        self._loop.set_exception_handler(self._on_exception)
        self._state: int = STATE_UNINITIALIZED
        self._state_start: float = self._loop.time()
        self._waits: dict = {}

    @property
    def exception(self) -> typing.Optional[Exception]:
        """If an exception was set with the state, return the value"""
        return self._exception

    @property
    def state(self) -> str:
        """Return the current state as descriptive string"""
        return self.state_description(self._state)

    def state_description(self, state: int) -> str:
        """Return a state description for a given state"""
        return self.STATE_MAP[state]

    @property
    def time_in_state(self) -> float:
        """Return how long the current state has been active"""
        return self._loop.time() - self._state_start

    def _clear_waits(self, wait_id: int) -> None:
        for state in self._waits.keys():
            if wait_id in self._waits[state].keys():
                del self._waits[state][wait_id]

    def _on_exception(self,
                      _loop: asyncio.AbstractEventLoop,
                      context: typing.Dict[str, typing.Any]) -> None:
        self._logger.debug('Exception on IOLoop: %r', context)
        self._set_state(STATE_EXCEPTION, context.get('exception'))

    def _reset_state(self, value: int) -> None:
        self._logger.debug(
            'Reset state %r while state is %r - %r',
            self.state_description(value), self.state, self._waits)
        self._state = value
        self._state_start = self._loop.time()
        self._exc = None
        self._waits = {}

    def _set_state(self, value: int,
                   exc: typing.Optional[Exception] = None) -> None:
        self._logger.debug(
            'Set state to %i: %s while state is %i: %s - %r [%r]',
            value, self.state_description(value), self._state, self.state,
            self._waits, exc)
        if value == self._state and exc == self._exception:
            return
        elif value != STATE_EXCEPTION \
                and value not in self.STATE_TRANSITIONS[self._state]:
            raise exceptions.StateTransitionError(
                'Invalid state transition from {!r} to {!r}'.format(
                    self.state, self.state_description(value)))
        self._logger.debug(
            'Transition to %i: %s from %i: %s after %.4f seconds',
            value, self.state_description(value),
            self._state, self.state, self.time_in_state)
        self._exception = exc
        self._state = value
        self._state_start = self._loop.time()
        if self._state in self._waits:
            [self._loop.call_soon(event.set)
             for event in self._waits[self._state].values()]

    async def _wait_on_state(self, *args) -> int:
        """Wait on a specific state value to transition"""
        wait_id, waits = time.monotonic_ns(), []
        self._logger.debug(
            'Waiter %i waiting on (%s) while in %i: %s',
            wait_id, ' || '.join(
                '{}: {}'.format(s, self.state_description(s))
                for s in args), self._state, self.state)
        for state in args:
            if state not in self._waits:
                self._waits[state] = {}
            self._waits[state][wait_id] = asyncio.Event()
            waits.append((state, self._waits[state][wait_id]))
        while not self._exception:
            for state, event in waits:
                if event.is_set():
                    self._logger.debug(
                        'Waiter %r wait on %i: %s has finished [%r]', wait_id,
                        state, self.state_description(state), self._exception)
                    self._clear_waits(wait_id)
                    return state
            await asyncio.sleep(0.001)
        self._clear_waits(wait_id)
        exc = self._exception
        self._exception = None
        raise exc
