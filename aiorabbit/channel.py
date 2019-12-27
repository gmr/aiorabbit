"""
Channel
=======

"""
import asyncio
import logging
import typing

from aiorabbit import state


class Channel(state.StateManager):

    STATE_UNINITIALIZED = 0x00
    STATE_OPENING = 0x01
    STATE_OPENED = 0x02
    STATE_CLOSING = 0x03
    STATE_CLOSED = 0x04
    STATE: dict = {
        0x00: 'Uninitialized',
        0x01: 'Opening',
        0x02: 'Opened',
        0x03: 'Closed'
    }
    STATE_MAP: dict = {
        STATE_UNINITIALIZED: {STATE_OPENING},
        STATE_OPENING: {STATE_OPENED, STATE_CLOSED},
        STATE_OPENED: {STATE_CLOSING, STATE_CLOSED},
        STATE_CLOSING: {STATE_CLOSED}
    }

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(loop)
