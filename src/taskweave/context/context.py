from typing import Pattern
import os, re
from dataclasses import dataclass
from .args_parser import get_config
config, args = get_config()

@dataclass
class Constants():
    log_folder = "logs/"

constants = Constants()
os.makedirs(constants.log_folder, exist_ok = True)

def get_app_context():
    return config, constants, args