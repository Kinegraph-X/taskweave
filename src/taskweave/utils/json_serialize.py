from typing import Any
from enum import Enum
from dataclasses import is_dataclass, fields

def jsonSerialize(obj: Any) -> Any:
    """
    Recursive JSON-compatible serialiser.
    Covers : dataclasses, Enums, listes, dicts, scalars.
    Callables (on_finally, etc.) are ignored — non-serialisable &
    unsupported in full-web (cf. doc SessionGateway).
    """
    if isinstance(obj, Enum):
        return obj.value
 
    if is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            if callable(value) and not is_dataclass(value):
                # on_finally, on_cancel, etc. — ignorés volontairement
                continue
            serialized = jsonSerialize(value)
            if serialized is not None:
                result[f.name] = serialized
        return result
 
    if isinstance(obj, list):
        return [jsonSerialize(item) for item in obj]
 
    if isinstance(obj, dict):
        return {k: jsonSerialize(v) for k, v in obj.items()}
 
    # scalaires : str, int, float, bool, None
    return obj

def parse_enum(enum_class: type[Enum], value: str | None, default: Enum | None = None) -> Enum | None:
    """
    Parses a string to an Enum, returns default if absent.
    Searches on .value first, then on .name.
    """
    if value is None:
        return default
    for member in enum_class:
        if member.value == value or member.name == value:
            return member
    return default