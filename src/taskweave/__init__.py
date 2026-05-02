import logging
from taskweave.context import get_app_context
config, constants, args = get_app_context()

logging.basicConfig(
    level = config.log_level,
    format = "%(asctime)s [%(name)s] %(levelname)s — %(message)s"
)