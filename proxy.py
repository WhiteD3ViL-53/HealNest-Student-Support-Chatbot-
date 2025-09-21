#!/usr/bin/env python3
import os, time, requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

MAIN = os.environ.get("MAIN_TARGET", "http://127.0.0.1:8601")
ADMIN = os.environ.get("ADMIN_TARGET", "http://127.0.0.1:8602")
PORT = int(os.environ.get("PORT", 8501))

def _forward_and_log(target_base, strip_prefix=None):
    # Build forward path
    path = request.path or "/"
    query = ("?" + request.query_string.decode()) if request.query_string else ""
    # strip prefix if requested (e.g. /admin)
    if strip_prefix and path.startswith(strip_prefix):
        forward_path = path[len(strip_prefix):] or "/"
    else:
        forward_path = path
    if not forward_path.startswith("/"):
        forward_path = "/" + forward_path

    forward_full = forward_path + (query if query else "")
    target_url = target_base.rstrip("/") + forward_full

    # copy headers (exclude hop-by-hop + host)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host","connection","content-length","transfer-encoding")}

    start = time.time()
    try:
        resp = requests.request(method=request.method, url=target_url, headers=headers,
                                data=request.get_data(), stream=True, timeout=30)
    except Exception as e:
        dur = time.time() - start
        print(f"[proxy] ERROR forward -> {target_url} method={request.method} dur={dur:.2f}s exc={e}")
        return Response(f"Upstream request failed: {e}", status=502)

    dur = time.time() - start
    print(f"[proxy] forward -> {target_url} method={request.method} status={resp.status_code} dur={dur:.2f}s remote={target_base}")

    # filter response headers and stream back
    excluded_resp = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded_resp]

    return Response(stream_with_context(resp.iter_content(chunk_size=8192)), status=resp.status_code, headers=resp_headers)


@app.route("/admin", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@app.route("/admin/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
def proxy_admin(path):
    return _forward_and_log(ADMIN, strip_prefix="/admin")


@app.route("/", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@app.route("/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
def proxy_main(path):
    return _forward_and_log(MAIN, strip_prefix=None)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
