# -*- coding: utf-8 -*-
"""
骑行路线设计器 - 本地服务器
用法:  python server.py   然后浏览器打开 http://127.0.0.1:8765

功能:
  1. 静态文件服务(本目录)
  2. /proxy/opentopodata/...  -> https://api.opentopodata.org/v1/...   (高程数据, 解决 CORS)
  3. /proxy/brouter?...       -> https://brouter.de/brouter?...        (OSM 骑行路由, 网络可达时用)
  4. /proxy/amap/...          -> https://restapi.amap.com/...          (高德 API 备用通道)
仅使用 Python 标准库, 无需安装依赖。
"""
import http.server
import json
import os
import socketserver
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.dirname(os.path.abspath(__file__))

UPSTREAMS = {
    '/proxy/opentopodata/': 'https://api.opentopodata.org/v1/',
    '/proxy/brouter':       'https://brouter.de/brouter',
    '/proxy/amap/':         'https://restapi.amap.com/',
    '/proxy/photon':        'https://photon.komoot.io',
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # ---------- 代理 ----------
    def do_GET(self):
        for prefix, upstream in UPSTREAMS.items():
            if self.path.startswith(prefix):
                return self.proxy(upstream + self.path[len(prefix):])
        return super().do_GET()

    def proxy(self, url):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'cycleroute-local/1.0',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                self._reply(r.status, r.read(), r.headers.get('Content-Type', 'application/json'))
        except urllib.error.HTTPError as e:
            self._reply(e.code, e.read(), e.headers.get('Content-Type', 'application/json'))
        except Exception as e:  # 网络不可达 / 超时
            try:
                body = json.dumps({'error': 'proxy failed: %s' % e}).encode('utf-8')
                self._reply(502, body, 'application/json')
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass  # 浏览器提前断开,忽略

    def _reply(self, status, body, ctype):
        try:
            self.send_response(status)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # 浏览器提前断开,忽略

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, TimeoutError):
            self.close_connection = True

    def log_message(self, fmt, *args):
        try:
            sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))
        except Exception:
            pass


class ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    httpd = ThreadingServer(('127.0.0.1', PORT), Handler)
    print('骑行路线设计器已启动: http://127.0.0.1:%d  (Ctrl+C 停止)' % PORT)
    print('代理通道: opentopodata(高程) / brouter(OSM 路由) / amap(高德)')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
