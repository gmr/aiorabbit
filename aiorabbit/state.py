"""
State Manager
=============

"""
import asyncio
import inspect
import logging
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

    def _on_exception(self,
                      _loop: asyncio.AbstractEventLoop,
                      context: typing.Dict[str, typing.Any]) -> None:
        self._logger.debug('Exception on IOLoop: %r', context)
        self._set_state(STATE_EXCEPTION, context['exception'])

    def _set_state(self, value: int,
                   exc: typing.Optional[Exception] = None) -> None:
        self._logger.debug('state: %r (%r) [%r], value: %r (%r) [%r]',
                           self.state, self._state, self._exception,
                           self.state_description(value), value, exc)
        if value == STATE_EXCEPTION or exc:
            self._exception = exc
            self._state = STATE_EXCEPTION
        else:
            if value == self._state:
                raise exceptions.StateTransitionError(
                    'Attempted to reassign the same state: {!r}'.format(
                        self.state))
            elif value not in self.STATE_TRANSITIONS[self._state]:
                raise exceptions.StateTransitionError(
                    'Invalid state transition from {!r} to {!r}'.format(
                        self.state, self.state_description(value)))
            else:
                self._logger.debug('Transition to %s after %.4f seconds',
                                   self.STATE_MAP[value], self.time_in_state)
                self._state = value
                self._state_start = self._loop.time()
        if self._state in self._waits:
            self._waits[self._state].set()

    @property
    def exception(self) -> typing.Optional[Exception]:
        return self._exception

    async def _wait_on_state(self, *args) -> None:
        """Wait on a specific state value to transition"""
        events, states = [], []
        for state in args:
            event = asyncio.Event()
            states.append(self.STATE_MAP[state])
            events.append((event, self.STATE_MAP[state]))
            self._waits[state] = event
        self._logger.debug('Waiting on %s', ', '.join(states))
        waiting = True
        while waiting and not self._exception:
            for event, state in events:
                if event.is_set():
                    self._logger.debug('Wait on %r has finished', state)
                    waiting = False
                    break
            await asyncio.sleep(0.001)
        for state in args:
            del self._waits[state]
        if self._exception:
            exc = self._exception
            self._exception = None
            raise exc
