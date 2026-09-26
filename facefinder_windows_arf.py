"""Packaged Windows entry point for ARF Face Finder."""
from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

import facefinder


data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ARF Face Finder"
facefinder.DATA = data_dir
facefinder.MODELS = data_dir / "models"
facefinder.UPLOADS = data_dir / "uploads"
facefinder.CACHE = data_dir / "cache.sqlite3"


@facefinder.app.after_request
def apply_arf_brand(response):
    if response.content_type.startswith("text/html"):
        html = response.get_data(as_text=True)
        html = html.replace("<title>FaceFinder</title>", "<title>ARF Face Finder</title>")
        html = html.replace(">FaceFinder</a>", ">ARF Face Finder</a>")
        branding = (
            '<link rel="icon" href="/facefinder_static/arf-logo.png">'
            '<style>.brand>span{font-size:0;background:transparent '
            'url(/facefinder_static/arf-logo.png) center/contain no-repeat!important;'
            'border-radius:0!important}</style>'
        )
        html = html.replace("</head>", branding + "</head>")
        response.set_data(html)
    return response


if __name__ == "__main__":
    facefinder.setup()
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5173/")).start()
    facefinder.app.run(host="127.0.0.1", port=5173, debug=False, threaded=True)
