from dataclasses import dataclass

@dataclass(kw_only = True)
class CompletedTask:
    name : str