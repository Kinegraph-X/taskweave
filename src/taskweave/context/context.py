from typing import Pattern
import os, re
from dataclasses import dataclass
from .args_parser import get_config
config, args = get_config()

@dataclass
class Constants():
    log_folder = "logs/"
    log_index_filename = "log_index"
    log_index_extension = ".json"

constants = Constants()

def get_app_context():
    return config, constants, args