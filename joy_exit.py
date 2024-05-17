from typing import Callable
from queue import Queue

import linux_joystick_battisti456.known_controller_names as kc

from time import time, sleep
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

BUTTON1_NAMES = {
    'L1',#PS4, PS3
    'LB',#STEAM,XBOX360,XBOXONE,
}
BUTTON2_NAMES = {
    'START',#XBOX360,XBOXONE,STEAM
    'OPTIONS',#PS4,PS3
    'PLUS'
}
AMOUNT_OF_TIME = 4

hold_start:dict[int,float|None] = {1 : None, 2: None}

start_holding:float|None = None
def on_change(button:int,queue:Queue[bool]) -> Callable[[bool],None]:
    def to_return(value:bool):
        logger.info(f"button = {button}, value = {value}")
        if value:
            if hold_start[button] is None:
                hold_start[button] = time()
        else:
            if not any(hold_start[button] == None for button in hold_start):
                now = time()
                if all(now - hold_start[button] > AMOUNT_OF_TIME for button in hold_start):#type:ignore
                    queue.put(False)
            hold_start[button] = None
    return to_return
def controller_loop():
    current_game_pads:dict[int,kc.Gamepad] = {}
    queue = Queue()

    trigger1 = on_change(1,queue)
    trigger2 = on_change(2,queue)
    while queue.empty():
        logger.info("new loop")
        for i in current_game_pads:
            if current_game_pads[i].updateThread is None:
                logger.error(f"update thread on '{i}' is none")
            elif not current_game_pads[i].updateThread.running:#type:ignore
                logger.error(f"update thread on '{i}' has stopped")
        for i in kc.all_js_nums() - set(current_game_pads):
            if i != 2:
                continue
            val = kc.load_controller(i)
            if not val is None:
                logger.info(f"adding controller {i}")
                current_game_pads[i] = val
        for i in current_game_pads:
            js = current_game_pads[i]
            val = js.joystickFile.peek()
            #logger.info(f"peeked into '{i}' and saw '{val}'")
            if val:
                event_name, entity_name, final_value = js.getNextEvent(skipInit=False)
                logger.info(f"event = {event_name}, entity = {entity_name}, raw_entity = {isinstance(entity_name,int)}, value = {final_value}")
                if isinstance(final_value,bool):
                    if entity_name in BUTTON1_NAMES:
                        trigger1(final_value)
                    if entity_name in BUTTON2_NAMES:
                        trigger2(final_value)
                    
                
        #sleep(10)
    for game_pad in current_game_pads.values():
        del game_pad

def joy_exit():
    logger.warning(f"starting child")
    process = subprocess.Popen(sys.argv[1:])
    logger.info("starting to watch")
    controller_loop()
    logger.warning("killing child")
    process.kill()
    logger.warning("successful exit")

def joy_buttons():
    try:
        while True:
            chosen:int = -1
            available:set[int] = set()
            while not chosen in available:
                available:set[int] = kc.all_js_nums()
                print(f"The joysticks available are all in: {available}")
                inpt = input("Which one would you like to explore? ")
                if inpt.isdecimal():
                    chosen = int(inpt)
                    if not chosen in available:
                        print("I am sorry, that input is not currently available.")
                else:
                    print("I am sorry, I couldn't interpret that.")
            name = kc.get_name(chosen)
            print(f"This gamepad is named '{name}'.")
            gmpd = kc.load_controller(chosen)
            if gmpd is None:
                print("Sorry, something went wrong.")
                continue
            try:
                print("Beggining loop. Press Ctrl+C to break out of it.")
                while True:
                    event_name, entity_name, final_value = gmpd.getNextEvent()
                    print(f"event = {event_name}, entity = {entity_name}, raw_entity = {isinstance(entity_name,int)}, value = {final_value}")
            except KeyboardInterrupt:
                ...
    except KeyboardInterrupt:
        ...
if __name__ == '__main__':
    if len(sys.argv) > 1:
        logger.info(f"monitoring to control exit of {' '.join(sys.argv[1:])}")
        joy_exit()
    else:
        logger.info("exploring controller buttons")
        joy_buttons()
    