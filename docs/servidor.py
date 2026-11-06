from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os, webbrowser

os.chdir(Path(__file__).resolve().parent)
try:
    server = ThreadingHTTPServer(('127.0.0.1', 8879), SimpleHTTPRequestHandler)
except OSError:
    print('A porta 8879 está ocupada. Feche o outro servidor e execute novamente.')
    raise SystemExit(1)
print('Mapa disponível em http://localhost:8879 — Ctrl+C para encerrar.', flush=True)
webbrowser.open('http://localhost:8879')
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
