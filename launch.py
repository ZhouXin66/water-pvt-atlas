"""Optional loopback-only viewer for the offline HTML. Uses the Python standard library."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
APP = 'water-pvt-local'
PREFIX = '/__water_pvt__'
RUNTIME = ROOT / '.local'
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def allowed_host(self):
        return self.headers.get('Host') == urllib.parse.urlsplit(self.server.url).netloc

    def do_GET(self):
        if not self.allowed_host():
            self.reply(403, {'error': 'Invalid host'})
            return
        self.server.last_activity = time.monotonic()
        path = urllib.parse.urlsplit(self.path).path
        if path in ['/', '/index.html']:
            self.reply(200, (ROOT/'dist/index.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == PREFIX+'/status':
            self.reply(200, {'app': APP, 'root': str(ROOT)})
        elif path == '/favicon.ico':
            self.reply(204, b'', 'image/x-icon')
        else:
            self.reply(404, {'error': 'Not found'})

def running_url():
    try:
        address = json.loads((RUNTIME/'server.json').read_text(encoding='utf-8'))['url']
        parsed = urllib.parse.urlsplit(address)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1':
            return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(address+PREFIX+'/status', timeout=2) as response:
            info = json.load(response)
        return address if info.get('app') == APP and info.get('root') == str(ROOT) else None
    except (OSError, ValueError, KeyError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--idle-seconds', type=float, default=600)
    args = parser.parse_args()
    existing = running_url()
    if existing:
        if not args.no_browser:
            webbrowser.open(existing)
        print(existing, flush=True)
        return
    if not (ROOT/'dist/index.html').is_file():
        raise FileNotFoundError('dist/index.html is missing; run build.py first')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.url = f'http://127.0.0.1:{server.server_port}'
    server.last_activity = time.monotonic()
    server.timeout = 1
    RUNTIME.mkdir(exist_ok=True)
    (RUNTIME/'server.json').write_text(json.dumps({'url': server.url}), encoding='utf-8')
    print(server.url, flush=True)
    if not args.no_browser:
        webbrowser.open(server.url)
    try:
        while time.monotonic()-server.last_activity < args.idle_seconds:
            server.handle_request()
    finally:
        server.server_close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        RUNTIME.mkdir(exist_ok=True)
        (RUNTIME/'error.log').write_text(str(error), encoding='utf-8')
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(error), 'Water PVT', 16)
        raise
