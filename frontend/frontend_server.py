#!/usr/bin/env python3
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

BACKEND_URL = os.environ.get('LOG_ANALYZER_BACKEND', 'http://localhost:8000')
FRONTEND_PORT = int(os.environ.get('FRONTEND_PORT', '8001'))


class ProxyRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(404, 'Not found')

    def proxy_request(self, method):
        backend_path = self.path[len('/api/'):]
        parsed_path = urlparse(backend_path)
        target = BACKEND_URL.rstrip('/') + '/' + parsed_path.path.lstrip('/')
        if parsed_path.query:
            target += '?' + parsed_path.query

        headers = {k: v for k, v in self.headers.items() if k.lower() != 'host'}
        body = None
        if method == 'POST':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else None

        request = Request(target, data=body, method=method, headers=headers)
        try:
            with urlopen(request) as response:
                self.send_response(response.status)
                for name, value in response.getheaders():
                    if name.lower() == 'transfer-encoding':
                        continue
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(response.read())
        except HTTPError as error:
            self.send_response(error.code)
            for name, value in error.headers.items():
                if name.lower() == 'transfer-encoding':
                    continue
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(error.read())
        except URLError as error:
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'Backend unavailable: {error.reason}'.encode('utf-8'))
        except Exception as error:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'Proxy error: {error}'.encode('utf-8'))


def run_server():
    os.chdir(os.path.dirname(__file__))
    server_address = ('', FRONTEND_PORT)
    httpd = HTTPServer(server_address, ProxyRequestHandler)
    print(f'Serving frontend on http://localhost:{FRONTEND_PORT}')
    print(f'Proxying API requests to {BACKEND_URL}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping server...')
        httpd.server_close()


if __name__ == '__main__':
    run_server()
