from joystick import JoystickEvent, JoyStickEventManager, ButtonLabel
from time import time
import subprocess
import sys
import logging

LEVEL = logging.INFO - 1

logger = logging.getLogger()
logger.setLevel(LEVEL)
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

KEYS_TO_HOLD:set[ButtonLabel] = {
    'start',#plus
    'tl'#left bumper
}
HOLD_TIME = 4

current_keys:set[ButtonLabel] = set()

start_holding:float|None = None

manager = JoyStickEventManager()

@manager.on_event
def key_handler(event:JoystickEvent):
    global start_holding, current_keys
    if event.event_type == 'button':
        logger.info(f"received: num = {event.label}, val = {event.value}")
        if event.value:#start pressing
            current_keys.add(event.label)
            if current_keys.issuperset(KEYS_TO_HOLD) and start_holding is None:
                start_holding = time()
                logger.warning(f"started holding")
        else:#stop pressing
            if event.label in current_keys:
                current_keys.remove(event.label)
            if not start_holding is None:
                diff = time() - start_holding
                if diff > HOLD_TIME:
                    logger.warning(f"triggered exit at {diff} seconds of holding")
                    return True
            if event.label in KEYS_TO_HOLD:
                logger.warning(f"canceled holding")
                start_holding = None
    else:
        logger.info(f"received non-button keytype {event.event_type}")

        #print(f"{key.number} : {key.value}")

if __name__ == '__main__':
    logger.warning(f"starting child")
    process = subprocess.Popen(sys.argv[1:])
    logger.info("starting to watch")
    manager.main_loop()
    logger.warning("killing child")
    process.kill()
    logger.warning("successful exit")
    