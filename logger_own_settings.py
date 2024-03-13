# logger_own_settings.py

import sys
from loguru import logger
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

def mylogger():
    logger.remove()
    LEVEL_LOGGER = env_vars.get("LEVEL_LOGGER")
    logger.add("logs/logs.log", format="{time} :: {level} :: {file} :: {name} :: {line} :: {message}", level=LEVEL_LOGGER, serialize=False, rotation="10 MB", compression="zip", diagnose=False)
    logger.add(sys.stderr, level="INFO")  # Добавлен вывод в терминале с уровнем INFO

if __name__ == '__main__':
    mylogger()