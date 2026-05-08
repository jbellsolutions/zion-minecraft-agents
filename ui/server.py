#!/usr/bin/env python3
"""
Zion's Minecraft Mod Builder - Web UI Server
No pip installs needed — uses Python stdlib only.
"""
import http.server
import socketserver
import json
import subprocess
import os
import threading
import urllib.parse
from pathlib import Path

PORT = 8765
PROJECT_DIR = Path(__file__).parent.parent
UI_DIR = Path(__file__).parent

# Store the output of the last claude run
last_output = {"status": "idle", "text": "Ready to build!"}
running = False


def run_claude(request_text):
    global last_output, running
    running = True
    last_output = {"status": "running", "text": "Building your mod... this might take a few minutes!"}

    prompt = f"""
You are the orchestrator for Zion's Minecraft mod system.

Zion (age 5) wants: {request_text}

Follow the instructions in agents/orchestrator.md and make it happen.
Build it, deploy it, and restart the server. No questions asked.
"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Agent,TodoWrite"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=600
        )
        output = result.stdout or result.stderr or "Done!"
        last_output = {"status": "done", "text": output[-3000:] if len(output) > 3000 else output}
    except subprocess.TimeoutExpired:
        last_output = {"status": "done", "text": "Still working... check back in a minute!"}
    except FileNotFoundError:
        last_output = {"status": "error", "text": "Claude Code not found. Make sure it's installed!"}
    except Exception as e:
        last_output = {"status": "error", "text": str(e)}
    finally:
        running = False


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/status":
            self._json(200, last_output)
        elif self.path == "/library":
            library_path = PROJECT_DIR / "mods" / "library.json"
            try:
                with open(library_path) as f:
                    data = json.load(f)
                self._json(200, data)
            except FileNotFoundError:
                self._json(200, {"mods": []})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/build":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body)
            request_text = data.get("request", "").strip()

            if not request_text:
                self._json(400, {"error": "Empty request"})
                return

            if running:
                self._json(429, {"error": "Still working on your last request!"})
                return

            thread = threading.Thread(target=run_claude, args=(request_text,), daemon=True)
            thread.start()
            self._json(200, {"status": "started"})

        else:
            self._json(404, {"error": "Not found"})

    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress server logs


def main():
    os.chdir(UI_DIR)
    print(f"\n{'='*50}")
    print(f"  Zion's Minecraft Mod Builder is READY!")
    print(f"  Opening in browser...")
    print(f"{'='*50}\n")

    # Open browser
    subprocess.Popen(["open", f"http://localhost:{PORT}/index.html"])

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
