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
    STATE_MAP: dict = {}
    STATE_TRANSITIONS: dict = {}

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._logger = logging.getLogger(
            dict(inspect.getmembers(self))['__module__'])
        self._exception: typing.Optional[Exception] = None
        self._loop: asyncio.AbstractEventLoop = loop
        self._state: int = self.STATE_UNINITIALIZED
        self._state_start: float = self._loop.time()
        self._waits: dict = {}

    @property
    def state(self) -> str:
        """Return the current state as descriptive string"""
        return self.STATE_MAP[self._state]

    def _set_state(self, new_state: int,
                   exception: typing.Optional[Exception] = None) -> None:
        if new_state == self._state:
            self._logger.debug('Same state (%s) reassigned', self.state)
            self._state_start = self._loop.time()
            return
        elif new_state not in self.STATE_TRANSITIONS[self._state]:
            raise exceptions.StateTransitionError(
                'Invalid state transition from %r to %r',
                self.state, self.STATE_MAP[new_state])
        self._logger.debug('Transition from %s to %s after %.4f seconds',
                           self.state, self.STATE_MAP[new_state],
                           self._loop.time() - self._state_start)
        if exception:
            self._exception = exception
        self._state = new_state
        self._state_start = self._loop.time()
        if self._state in self._waits:
            self._waits[self._state].set()

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
