from typing import Callable, Literal, overload,Iterator
import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger()

type EventCallback = Callable[[JoystickEvent],bool|None]
"""
function to be called on all occuring JoystickEvents

if it returns True, main_loop will exit
"""
type EventType = Literal['button','axis']

#region ButtonLabel
type ButtonLabel = Literal[
    'trigger',
    'thumb',
    'thumb2',
    'top',
    'top2',
    'pinkie',
    'base',
    'base2',
    'base3',
    'base4',
    'base5',
    'base6',
    'dead',
    'a',
    'b',
    'c',
    'x',
    'y',
    'z',
    'tl',
    'tr',
    'tl2',
    'tr2',
    'select',
    'start',
    'mode',
    'thumbl',
    'thumbr',
    'dpad_up',
    'dpad_down',
    'dpad_left',
    'dpad_right',
]
#endregion
#region AxisLabel
type AxisLabel = Literal[
    'x',
    'y',
    'z',
    'rx',
    'ry',
    'rz',
    'throttle',
    'rudder',
    'wheel',
    'gas',
    'brake',
    'hat0x',
    'hat0y',
    'hat1x',
    'hat1y',
    'hat2x',
    'hat2y',
    'hat3x',
    'hat3y',
    'pressure',
    'distance',
    'tilt_x',
    'tilt_y',
    'tool_width',
    'volume',
    'misc'
]
#endregion

@dataclass(frozen = True)
class ButtonEvent():
    joystick_id:int
    event_type:Literal['button']
    label:ButtonLabel
    value:bool
@dataclass(frozen = True)
class AxisEvent():
    joystick_id:int
    event_type:Literal['axis']
    label:AxisLabel
    value:float
type JoystickEvent = ButtonEvent|AxisEvent
@overload
def make_event(joystick_id:int,event_type:Literal['axis'],label:AxisLabel,value:float) -> AxisEvent:
    ...
@overload
def make_event(joystick_id:int,event_type:Literal['button'],label:ButtonLabel,value:bool) -> ButtonEvent:
    ...
def make_event(joystick_id:int,event_type:EventType,label:ButtonLabel|AxisLabel,value:bool|float) -> JoystickEvent:
    if event_type == 'button':
        return ButtonEvent(joystick_id,event_type,label,value)#type:ignore
    else:
        return AxisEvent(joystick_id,event_type,label,value)#type:ignore

class JoyStickEventManager(object):
    def __init__(self):
        self.on_events:set[EventCallback] = set()
    def on_event(self,callback:EventCallback) -> EventCallback:
        self.on_events.add(callback)
        return callback
    def main_loop(self):
        event_iterator:Iterator[JoystickEvent]
        match(sys.platform):
            case 'posix':#linux based systems
                from joystick.linux_joystick import linux_js_events
                event_iterator = linux_js_events()
            case 'win32':#windows based systems
                logger.warning("Windows is not yet fully supported!!!!")
                from joystick.windows_joystick import windows_js_events
                event_iterator = windows_js_events()
            case _:
                raise Exception('not supported platform')
        for event in event_iterator:
            for on_event in self.on_events:
                val = on_event(event)
                if val:
                    return
        
