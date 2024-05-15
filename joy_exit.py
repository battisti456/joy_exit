from pyjoystick.sdl2 import Key, Joystick, run_event_loop,stop_event_wait
from time import time
import subprocess
import sys

class Exit(Exception):
    ...

KEYS_TO_HOLD = {
    7,#plus
    4#left bumper
}
HOLD_TIME = 4

current_keys:set[int] = set()

start_holding:float|None = None

def add_handler(joystick:Joystick):
    ...
def remove_handler(joystick:Joystick):
    ...
def key_handler(key:Key):
    global start_holding, current_keys
    if key.keytype is Key.BUTTON:
        if key.value:#start pressing
            current_keys.add(key.number)
            if current_keys.issuperset(KEYS_TO_HOLD) and start_holding is None:
                start_holding = time()
        else:#stop pressing
            if key.number in current_keys:
                current_keys.remove(key.number)
            if not start_holding is None:
                if time() - start_holding > HOLD_TIME:
                    raise Exit()
            if key.number in KEYS_TO_HOLD:
                start_holding = None

        #print(f"{key.number} : {key.value}")

if __name__ == '__main__':
    process = subprocess.Popen(sys.argv[1:])
    try:
        run_event_loop(add_handler,remove_handler,key_handler)
    except Exit:
        ...
    process.kill()
    