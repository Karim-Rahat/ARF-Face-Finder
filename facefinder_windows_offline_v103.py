"""ARF Face Finder 1.0.3: offline build with corrected selection."""
from __future__ import annotations

import threading
import webbrowser

import facefinder
import facefinder_windows_offline as offline


@facefinder.app.after_request
def apply_selection_fix(response):
    if response.content_type.startswith("text/html"):
        html = response.get_data(as_text=True)
        assets = (
            '<style>.gallery,.actionbar,.photo-card{user-select:none;-webkit-user-select:none}</style>'
            '<script src="/facefinder_static/selection-fix.js"></script>'
        )
        html = html.replace("</body>", assets + "</body>")
        response.set_data(html)
    return response


if __name__ == "__main__":
    facefinder.setup()
    offline.install_bundled_models()
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5173/")).start()
    facefinder.app.run(host="127.0.0.1", port=5173, debug=False, threaded=True)
