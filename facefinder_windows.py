"""Windows packaged entry point for FaceFinder."""
from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

import facefinder


data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FaceFinder"
facefinder.DATA = data_dir
facefinder.MODELS = data_dir / "models"
facefinder.UPLOADS = data_dir / "uploads"
facefinder.CACHE = data_dir / "cache.sqlite3"


if __name__ == "__main__":
    facefinder.setup()
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5173/")).start()
    facefinder.app.run(host="127.0.0.1", port=5173, debug=False, threaded=True)
