#!/usr/nin/python3
import coloredlogs, logging

logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

try:
    from config.config import *
except Exception as e:
    logger.critical("config file not found")
    raise Exception(e)
