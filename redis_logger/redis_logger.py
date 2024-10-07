"""
Check redis python documentation
https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Self

from redis_logger.schemas import SRedisLogger


class RedisLogger(logging.Logger):
    def __init__(self: Self, *args, config: SRedisLogger, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._config = config
        self._logger = logging.getLogger(self._config.name)
        # TODO get log format, log_level parameter from config
        self._handler = RedisHandler(*args, **kwargs)
        # Decide how we run in async emit function in other thread or current thread
        self._executor: ThreadPoolExecutor

    def log(self: Self, level: int, msg: str): ...

    def debug(self: Self, msg: str): ...

    # TODO overwrite other log methods


class RedisHandler(logging.Handler):
    """
    Basically, we overwrite logging handler emit method, we can
    change log destination. If we add that handler to our logger class
    logs are wrote our new log destination.
    https://dev.to/salemzii/writing-custom-log-handlers-in-python-58bi
    ./example_smtp_logger.py
    """

    def __init__(self: Self, host, port, username, password):
        ...
        # TODO create constructor for handler initializing.

    def emit(self, record: logging.LogRecord):
        ...
        # TODO create emit method for redis logger

    async def _emit(self, record: logging.LogRecord):
        ...
        # TODO to async part of redis logger
