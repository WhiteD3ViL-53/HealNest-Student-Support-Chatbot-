#!/usr/bin/env python3
import os
import requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

MAIN_TARGET = os.environ.get("MAIN_TARGET", "http://127.0.0.1:8601")
ADMIN_TARGET = os.environ.get("ADMIN_TARGET", "http://127.0.0.1:8602")
PORT = int(os.environ.get("PORT", 8501))


def _proxy_request(target_base, strip_prefix=None):
    path = request.full_path   # includes "path?query"
    if path.endswith("?"):
        path = path[:-1]

    # Strip prefix if needed
    if strip_prefix and path.startswith(strip_prefix):
        forward_path = path[len(strip_prefix):]
    else:
        forward_path = path

    # Ensure it starts with "/"
    if not forward_path.startswith("/"):
        forward_path = "/" + forward_path

    target_url = target_base + forward_path

    # Copy headers except hop-by-hop
    excluded = {"host", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded}

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            stream=True,
            timeout=30,
        )
    except Exception as e:
        return Response(f"Upstream request failed: {e}", status=502)

    excluded_resp = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded_resp]

    return Response(
        stream_with_context(resp.iter_content(chunk_size=8192)),
        status=resp.status_code,
        headers=resp_headers,
    )


@app.route("/admin", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@app.route("/admin/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
def proxy_admin(path):
    # strip "/admin" prefix
    return _proxy_request(ADMIN_TARGET, strip_prefix="/admin")


@app.route("/", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
@app.route("/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"])
def proxy_main(path):
    return _proxy_request(MAIN_TARGET)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
