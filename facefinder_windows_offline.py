"""Fully offline packaged Windows entry point for ARF Face Finder."""
from __future__ import annotations

import os
import re
import shutil
import sys
import threading
import webbrowser
from pathlib import Path

import facefinder


resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ARF Face Finder"
facefinder.DATA = data_dir
facefinder.MODELS = data_dir / "models"
facefinder.UPLOADS = data_dir / "uploads"
facefinder.CACHE = data_dir / "cache.sqlite3"


def install_bundled_models() -> None:
    """Copy bundled models once; no download is needed on first scan."""
    facefinder.MODELS.mkdir(parents=True, exist_ok=True)
    bundled = resource_root / "offline_models"
    for name in facefinder.MODEL_URLS:
        source = bundled / name
        destination = facefinder.MODELS / name
        if not destination.exists() or destination.stat().st_size < 100_000:
            shutil.copy2(source, destination)


@facefinder.app.after_request
def apply_offline_arf_brand(response):
    if response.content_type.startswith("text/html"):
        html = response.get_data(as_text=True)
        html = re.sub(r'<link[^>]+(?:fonts\.googleapis|fonts\.gstatic)[^>]*>', "", html)
        html = html.replace("<title>FaceFinder</title>", "<title>ARF Face Finder</title>")
        html = html.replace(">FaceFinder</a>", ">ARF Face Finder</a>")
        branding = (
            '<link rel="icon" href="/facefinder_static/arf-logo.png">'
            '<style>body{font-family:Segoe UI,Arial,sans-serif!important}'
            '.brand,.intro h1,.results-head h1,.step h2,.modal h2,.primary{font-family:Segoe UI,Arial,sans-serif!important}'
            '.brand>span{font-size:0;background:transparent url(/facefinder_static/arf-logo.png) '
            'center/contain no-repeat!important;border-radius:0!important}</style>'
        )
        html = html.replace("</head>", branding + "</head>")
        response.set_data(html)
    return response


if __name__ == "__main__":
    facefinder.setup()
    install_bundled_models()
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5173/")).start()
    facefinder.app.run(host="127.0.0.1", port=5173, debug=False, threaded=True)
