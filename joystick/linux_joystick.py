# Based on this: https://gist.github.com/rdb/8864666
from joystick import logger, JoystickEvent, ButtonLabel, AxisLabel, make_event

import os, struct, array
from fcntl import ioctl# type: ignore

from typing import TYPE_CHECKING, IO, Iterator
if TYPE_CHECKING:
    global iotcl
    def ioctl(fd:IO[bytes],request:int,arg:int|bytes|bytearray|array.array[int]=0,mutate_flag=True):
        ...

INPUT_PATH = '/dev/input'
PREFIX = 'js'

# Iterate over the joystick devices.
print('Available devices:')

for fn in os.listdir('/dev/input'):
    if fn.startswith('js'):
        print('  /dev/input/%s' % (fn))

# These constants were borrowed from linux/input.h
axis_names:dict[int,AxisLabel] = {
    0x00 : 'x',
    0x01 : 'y',
    0x02 : 'z',
    0x03 : 'rx',
    0x04 : 'ry',
    0x05 : 'rz',
    0x06 : 'throttle',
    0x07 : 'rudder',
    0x08 : 'wheel',
    0x09 : 'gas',
    0x0a : 'brake',
    0x10 : 'hat0x',
    0x11 : 'hat0y',
    0x12 : 'hat1x',
    0x13 : 'hat1y',
    0x14 : 'hat2x',
    0x15 : 'hat2y',
    0x16 : 'hat3x',
    0x17 : 'hat3y',
    0x18 : 'pressure',
    0x19 : 'distance',
    0x1a : 'tilt_x',
    0x1b : 'tilt_y',
    0x1c : 'tool_width',
    0x20 : 'volume',
    0x28 : 'misc',
}

button_names:dict[int,ButtonLabel] = {
    0x120 : 'trigger',
    0x121 : 'thumb',
    0x122 : 'thumb2',
    0x123 : 'top',
    0x124 : 'top2',
    0x125 : 'pinkie',
    0x126 : 'base',
    0x127 : 'base2',
    0x128 : 'base3',
    0x129 : 'base4',
    0x12a : 'base5',
    0x12b : 'base6',
    0x12f : 'dead',
    0x130 : 'a',
    0x131 : 'b',
    0x132 : 'c',
    0x133 : 'x',
    0x134 : 'y',
    0x135 : 'z',
    0x136 : 'tl',
    0x137 : 'tr',
    0x138 : 'tl2',
    0x139 : 'tr2',
    0x13a : 'select',
    0x13b : 'start',
    0x13c : 'mode',
    0x13d : 'thumbl',
    0x13e : 'thumbr',

    0x220 : 'dpad_up',
    0x221 : 'dpad_down',
    0x222 : 'dpad_left',
    0x223 : 'dpad_right',

    # XBox 360 controller uses these codes.
    0x2c0 : 'dpad_left',
    0x2c1 : 'dpad_right',
    0x2c2 : 'dpad_up',
    0x2c3 : 'dpad_down',
}

class LinuxJoystick(object):
    def __init__(self,num:int = 0):
        self.num = 0
        self.path = f"{INPUT_PATH}/{PREFIX}{num}"
        self.info("opening...")
        self.dev = open(
            self.path,
            'rb'
        )
        self.info("extracting name...")
        buf = array.array('B', [0] * 64)
        ioctl(self.dev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        self.name:str = buf.tobytes().rstrip(b'\x00').decode('utf-8')
        self.info(f"name = {self.name}")

        self.info("extracting num_axes...")
        buf = array.array('B', [0])
        ioctl(self.dev, 0x80016a11, buf) # JSIOCGAXES
        self.num_axes= buf[0]
        self.info(f"num_axes = {self.num_axes}")
        
        self.info("extracting num_buttons...")
        buf = array.array('B', [0])
        ioctl(self.dev, 0x80016a12, buf) # JSIOCGBUTTONS
        self.num_buttons = buf[0]
        self.info("num_buttons = self.num_buttons")

        self.info("extracting axis_map...")
        self.axis_map:list[AxisLabel] = []
        buf = array.array('B', [0] * 0x40)
        ioctl(self.dev, 0x80406a32, buf) # JSIOCGAXMAP

        for axis in buf[:self.num_axes]:
            axis_name:AxisLabel = axis_names.get(axis, 'unknown(0x%02x)' % axis)#type: ignore
            self.axis_map.append(axis_name)
            #axis_states[axis_name] = 0.0
        self.info(f"axis_map = {self.axis_map}")

        self.info("extracting button_map...")
        self.button_map:list[ButtonLabel] = []
        buf = array.array('H', [0] * 200)
        ioctl(self.dev, 0x80406a34, buf) # JSIOCGBTNMAP

        for btn in buf[:self.num_buttons]:
            btn_name:ButtonLabel = button_names.get(btn, 'unknown(0x%03x)' % btn)#type: ignore
            self.button_map.append(btn_name)
            #button_states[btn_name] = 0
        self.info(f"button_map = {self.button_map}")
    def __hash__(self) -> int:
        return self.num
    def info(self,text:str):
        logger.info(f"js{self.num}: {text}")
    def debug(self,text:str):
        logger.debug(f"js{self.num}: {text}")
    def read(self) -> JoystickEvent|None:
        evbuf = self.dev.read(8)
        if evbuf:
            time:int
            value:int
            _type:int
            number:int
            time, value, _type, number = struct.unpack('IhBB', evbuf)
            self.debug(f"received: time = {time}, value = {value}, type = {_type}, number = {number}")
            if _type & 0x80:
                self.debug("intialized...")
            if _type & 0x01:
                button = self.button_map[number]
                return make_event(
                    self.num,
                    'button',
                    button,
                    bool(value)
                )
            if _type & 0x02:
                axis = self.axis_map[number]
                fvalue:float = value / 32767.0
                return make_event(
                    self.num,
                    'axis',
                    axis,
                    fvalue
                )
def get_available_js() -> set[int]:
    return set(int(_input[len(PREFIX):]) for _input in os.listdir(INPUT_PATH) if _input.startswith(PREFIX))
def linux_js_events() -> Iterator[JoystickEvent]:
    joys:set[LinuxJoystick] = set()
    while True:
        new_jss:set[int] = get_available_js() - set(joy.num for joy in joys)
        for new_js in new_jss:
            joys.add(LinuxJoystick(new_js))
        bad_joys:set[LinuxJoystick] = set()
        for joy in joys:
            try:
                val = joy.read()
                if not val is None:
                    yield val
            except IOError:
                bad_joys.add(joy)
        joys -= bad_joys

