import os
import logging

logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "INFO"),
    format="%(asctime)s - [%(levelname)s]: %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName(os.getenv("LOGGING_LEVEL", "INFO")))
formatter = logging.Formatter("%(asctime)s - [%(levelname)s]: %(message)s")


logger.info("-----------------------------------")
logger.info(
    "Logger initialized with level {}".format(os.getenv("LOGGING_LEVEL", "INFO"))
)
