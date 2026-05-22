"""Windows DLL path setup for llama-cpp-python (CPU and CUDA builds)."""

import os
import sys
from pathlib import Path


def setup_dll_paths() -> None:
    if sys.platform != "win32":
        return

    site_packages = None
    for p in sys.path:
        sp = Path(p)
        if sp.name == "site-packages" and sp.is_dir():
            site_packages = sp
            break

    if site_packages is None:
        return

    dll_dirs = [
        site_packages / "llama_cpp" / "lib",
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cuda_runtime" / "bin",
        site_packages / "nvidia" / "cuda_nvrtc" / "bin",
    ]

    for ver in ("12.9", "12.8", "12.6", "12.4", "12.2", "12.1"):
        toolkit = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA") / f"v{ver}" / "bin"
        if toolkit.is_dir():
            dll_dirs.append(toolkit)

    for d in dll_dirs:
        if d.is_dir():
            try:
                os.add_dll_directory(str(d))
            except (AttributeError, OSError):
                pass
            os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")


setup_dll_paths()
