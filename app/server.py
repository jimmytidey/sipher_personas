#!/usr/bin/env python
"""Simple static file server for the SIPHER Personas web app.

Run from the project root:
    python app/server.py

Or from the app/ directory:
    python server.py

Then open http://localhost:3000 in your browser.
The API must be running separately on http://localhost:8000:
    uvicorn api.main:app --reload
"""

import http.server
import os
import socketserver

PORT = 3000

# Serve files from the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Suppress noisy request logs; print a clean version
        print(f"  {self.address_string()} -> {args[0]}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"SIPHER Personas app running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
