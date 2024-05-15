import logging
from time import sleep

logger = logging.getLogger()
logger.addHandler(logging.FileHandler('test.txt'))

i = 0
while True:
    logger.warning(str(i))
    sleep(1)
    i += 1