"""
State Manager
=============

"""
import asyncio
import inspect
import logging
import typing

from aiorabbit import exceptions


class StateManager:
    """Base Class used to implement state management"""

    STATE_UNINITIALIZED = 0x00
    STATE_EXCEPTION = 0x01
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
        self._state: int = self.STATE_UNINITIALIZED
        self._state_start: float = self._loop.time()
        self._waits: dict = {}

    @property
    def state(self) -> str:
        """Return the current state as descriptive string"""
        return self.STATE_MAP[self._state]

    def _on_exception(self,
                      _loop: asyncio.AbstractEventLoop,
                      context: typing.Dict[str, typing.Any]) -> None:
        self._logger.debug('Exception on IOLoop: %r', context)
        self._set_state(self.STATE_EXCEPTION, context['exception'])

    def _set_state(self, new_state: int,
                   exc: typing.Optional[Exception] = None) -> None:
        self._logger.debug('Set state: %r [%r] - Current: %r',
                           self.STATE_MAP[new_state], exc, self.state)
        if new_state == self._state:
            self._logger.debug('Ignoring state reassignment (%r)', self.state)
            return
        elif new_state not in self.STATE_TRANSITIONS[self._state] \
                and new_state != self.STATE_EXCEPTION:
            raise exceptions.StateTransitionError(
                'Invalid state transition from {!r} to {!r}'.format(
                    self.state, self.STATE_MAP[new_state]))
        self._logger.debug('Transition to %s after %.4f seconds',
                           self.STATE_MAP[new_state],
                           self._loop.time() - self._state_start)
        if exc:
            self._exception = exc
            if new_state != self.STATE_EXCEPTION:
                new_state = self.STATE_EXCEPTION
                self._logger.debug('Forcing exception state instead of %r',
                                   self.STATE_MAP[new_state])
        self._state = new_state
        self._state_start = self._loop.time()
        if self._state in self._waits:
            self._waits[self._state].set()
        self._logger.debug('Current state: %r [%r]',
                           self.state, self.exception)

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
