"""QuantForge - local GGUF quantization and inference toolkit."""

from importlib.metadata import PackageNotFoundError, version


def _read_version() -> str:
    try:
        return version("quantforge")
    except PackageNotFoundError:
        from pathlib import Path

        for parent in Path(__file__).resolve().parents:
            version_file = parent / "VERSION"
            if version_file.is_file():
                return version_file.read_text(encoding="utf-8").strip()
        return "0.0.0.dev"


__version__ = _read_version()
