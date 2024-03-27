# logger_own_settings.py

import sys
from loguru import logger
from dotenv import dotenv_values


def mylogger() -> None:
    logger.remove()
    env_vars = dotenv_values(".env")
    LEVEL_LOGGER: str = env_vars.get("LEVEL_LOGGER") or "INFO"  # По умолчанию устанавливаем уровень логгирования INFO

    logger.add("logs/logs.log", format="{time} :: {level} :: {file} :: {name} :: {line} :: {message}", level=LEVEL_LOGGER, serialize=False, rotation="10 MB", compression="zip", diagnose=False)
    logger.add(sys.stderr, level=LEVEL_LOGGER)  # Добавлен вывод в терминале с уровнем INFO

def test_logger() -> None:
    logger.remove()
    env_vars = dotenv_values(".env")
    LEVEL_LOGGER: str = env_vars.get("LEVEL_LOGGER") or "INFO"  # По умолчанию устанавливаем уровень логгирования INFO

    logger.add("tests/logs/logs.log", format="{time} :: {level} :: {file} :: {name} :: {line} :: {message}", level=LEVEL_LOGGER, serialize=False, rotation="10 MB", compression="zip", diagnose=False)
    logger.add(sys.stderr, level=LEVEL_LOGGER)  # Добавлен вывод в терминале с уровнем INFO

if __name__ == '__main__':
    mylogger()
