from taskweave_protocol import JsonSchemaType

def cast_bool(v: str) -> bool:
    v = v.strip().lower()

    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid bool: {v!r}")

DIALECT_CAST = {
    JsonSchemaType.INT : int,
    JsonSchemaType.FLOAT : float,
    JsonSchemaType.STRING : str,
    JsonSchemaType.BOOL : cast_bool
}