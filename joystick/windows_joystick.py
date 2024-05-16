from joystick import JoystickEvent, make_event
from typing import Iterator

from pyjoystick.sdl2 import Key, Joystick, EventLoop, joystick_key_from_event, controller_key_from_event


def windows_js_events() -> Iterator[JoystickEvent]:
    evl = EventLoop()
    for event in evl:
        key:Key|None = joystick_key_from_event(event)
        if key is None:
            key = controller_key_from_event(event)
        if not key is None:
            yield make_event(
                key.joystick.get_id(),#type:ignore
                'button',
                key.keyname,#type:ignore
                key.value
            )#type:ignore:
    #other events not implemented
    