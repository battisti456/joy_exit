from pyjoystick.sdl2 import Key, Joystick, run_event_loop,stop_event_wait
from time import time
import subprocess
import sys
import logging

LEVEL = logging.INFO

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s::%(levelname)-8s::%(message)s")
handlers:set[logging.Handler] = {
    logging.FileHandler(
        'joy_exit.log'
    ),
    logging.StreamHandler()
}
for handler in handlers:
    handler.setFormatter(formatter)
    handler.setLevel(LEVEL)
    logger.addHandler(handler)

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
    logger.warning(f"connected joystick {joystick}")
def remove_handler(joystick:Joystick):
    logger.warning(f"diconnected joystick {joystick}")
def key_handler(key:Key):
    global start_holding, current_keys
    if key.keytype is Key.BUTTON:
        logger.info(f"received: num = {key.number}, val = {key.value}")
        if key.value:#start pressing
            current_keys.add(key.number)
            if current_keys.issuperset(KEYS_TO_HOLD) and start_holding is None:
                start_holding = time()
                logger.warning(f"started holding")
        else:#stop pressing
            if key.number in current_keys:
                current_keys.remove(key.number)
            if not start_holding is None:
                diff = time() - start_holding
                if diff > HOLD_TIME:
                    logger.warning(f"triggered exit at {diff} seconds of holding")
                    raise Exit()
            if key.number in KEYS_TO_HOLD:
                logger.warning(f"canceled holding")
                start_holding = None

        #print(f"{key.number} : {key.value}")

if __name__ == '__main__':
    logger.warning(f"starting child")
    process = subprocess.Popen(sys.argv[1:])
    try:
        logger.info("starting to watch")
        run_event_loop(add_handler,remove_handler,key_handler)
    except Exit:
        ...
    logger.info("killing child")
    process.kill()
    logger.info("successful exit")
    