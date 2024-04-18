import os


def getenv_or_fail(key, default: str = None) -> str:
    val = os.getenv(key, default)
    if not val:
        raise RuntimeError(f"missing {key}")
    return val


def getenv_bool(key, default: bool | None = None) -> bool | None:
    val = os.getenv(key)
    if not val:
        return default
    val = val.lower()
    if val not in ("true", "false", "1", "0"):
        raise RuntimeError(f"invalid value '{val}' for {key}")
    return val not in ("false", "0")
