"""Formatting helpers."""


def format_time(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.2f} sec"


def format_size(bytes_size: int | float) -> str:
    b = float(bytes_size)
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024.0:
            return f"{b:.2f} {unit}"
        b /= 1024.0
    return f"{b:.2f} TB"
