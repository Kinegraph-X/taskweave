import logging
from whisper_infer.context import get_app_context
config, constants = get_app_context()

logging.basicConfig(
    level = config.log_level,
    format = "%(asctime)s [%(name)s] %(levelname)s — %(message)s"
)