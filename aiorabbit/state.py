"""
State Manager
=============

"""
import asyncio
import logging
import typing

LOGGER = logging.getLogger(__name__)


class StateManager:
    """Base Class used to implement state management"""

    STATE_UNINITIALIZED = 0x00
    STATE_MAP: dict = {}
    STATE_TRANSITIONS: dict = {}

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop: asyncio.AbstractEventLoop = loop
        self._state: int = self.STATE_UNINITIALIZED
        self._state_start: float = self._loop.time()

    def _set_state(self, new_state: int) -> typing.NoReturn:
        if new_state == self._state:
            LOGGER.debug('Same state (%s) reassigned',
                         self.STATE_MAP[self._state])
            self._state_start = self._loop.time()
            return
        if new_state not in self.STATE_TRANSITIONS[self._state]:
            raise RuntimeError('Invalid state transition %s to %s',
                               self.STATE_MAP[self._state],
                               self.STATE_MAP[new_state])
        LOGGER.debug('Transitioning from %s to %s after %.2f seconds',
                     self.STATE_MAP[self._state], self.STATE_MAP[new_state],
                     self._loop.time() - self._state_start)
        self._state = new_state
        self._state_start = self._loop.time()
