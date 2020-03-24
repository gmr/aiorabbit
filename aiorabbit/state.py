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
        self._waiting: int = 0

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
            'Reset state %r while state is %r with %i waiting',
            self.state_description(value), self.state, self._waiting)
        self._state = value
        self._state_start = self._loop.time()
        self._exc = None
        self._waits = {}

    def _set_state(self, value: int,
                   exc: typing.Optional[Exception] = None) -> None:
        self._logger.debug(
            'Set state %r (%r) while state is %r with %i waiting',
            self.state_description(value), exc, self.state, self._waiting)
        if value == STATE_EXCEPTION or exc:
            self._logger.debug('Exception passed in with state: %r', exc)
            self._exception = exc
            self._state = STATE_EXCEPTION
        else:
            if value == self._state:
                pass
            elif value not in self.STATE_TRANSITIONS[self._state]:
                raise exceptions.StateTransitionError(
                    'Invalid state transition from {!r} to {!r}'.format(
                        self.state, self.state_description(value)))
            else:
                self._logger.debug(
                    'Transition to %r (%i) from %r (%i) after %.4f seconds',
                    self.state_description(value), value,
                    self.state, self._state, self.time_in_state)
                self._state = value
                self._state_start = self._loop.time()
        if self._state in self._waits:
            [self._loop.call_soon(event.set)
             for event in self._waits[self._state].values()]

    async def _wait_on_state(self, *args) -> int:
        """Wait on a specific state value to transition"""
        self._waiting += 1
        wait_id, waits = time.monotonic_ns(), []
        for state in args:
            if state not in self._waits and state != self._state:
                self._waits[state] = {}
            self._waits[state][wait_id] = asyncio.Event()
            waits.append((state, self._waits[state][wait_id]))
        self._logger.debug(
            'Waiter %r waiting on %s', wait_id, ', '.join(
                ['({}) {}'.format(s, self.state_description(s[0]))
                 for s in waits]))
        while not self._exception:
            for state, event in waits:
                if event.is_set():
                    self._logger.debug(
                        'Waiter %r wait on %r (%i) has finished', wait_id,
                        self.state_description(state), state)
                    self._clear_waits(wait_id)
                    self._waiting -= 1
                    return state
            await asyncio.sleep(0.001)
        exc = self._exception
        self._exception = None
        self._waiting -= 1
        raise exc
