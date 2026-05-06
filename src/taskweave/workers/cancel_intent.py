from dataclasses import dataclass

@dataclass(kw_only = True)
class CancelIntent:
    name : str