"""Start the QuantForge web dashboard."""

from __future__ import annotations

import sys
import webbrowser


def run_web(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    open_browser: bool = True,
) -> int:
    try:
        import uvicorn
    except ImportError:
        print(
            'ERROR: Web dependencies missing. Install with:\n  pip install -e ".[web]"',
            file=sys.stderr,
        )
        return 1

    url = f"http://{host}:{port}/"
    print("QuantForge Dashboard")
    print(f"  URL:  {url}")
    print("  Bind: local only (do not expose to the internet without auth)")
    print()

    if open_browser:
        try:
            webbrowser.open(url)
        except OSError:
            pass

    uvicorn.run(
        "quantforge.web.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
    return 0
