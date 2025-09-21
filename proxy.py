#!/usr/bin/env python3
"""
proxy.py — reverse-proxy for two local Streamlit apps.

Routes:
- /        -> forwards to MAIN_TARGET (default http://127.0.0.1:8501)
- /admin   -> forwards to ADMIN_TARGET (default http://127.0.0.1:8502)

This file **forwards** requests server-side (no client redirects), streaming responses
back to the client. It reads MAIN_TARGET/ADMIN_TARGET from environment variables.
"""
import os
import requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

MAIN_TARGET = os.environ.get("MAIN_TARGET", "http://127.0.0.1:8501")
ADMIN_TARGET = os.environ.get("ADMIN_TARGET", "http://127.0.0.1:8502")
PORT = int(os.environ.get("PORT", 8080))


def _proxy_request(target_base):
    # Build target URL (preserve path + query)
    path = request.full_path
    if path.endswith("?"):
        path = path[:-1]
    target_url = target_base + path

    # copy headers except hop-by-hop and host
    excluded = {"host", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded}

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            stream=True,
            timeout=30,
        )
    except Exception as e:
        return Response(f"Upstream request failed: {e}", status=502)

    # filter response headers before sending back
    excluded_resp = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded_resp]

    return Response(
        stream_with_context(resp.iter_content(chunk_size=8192)),
        status=resp.status_code,
        headers=resp_headers,
    )


@app.route("/admin", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/admin/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_admin(path):
    return _proxy_request(ADMIN_TARGET)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_main(path):
    return _proxy_request(MAIN_TARGET)


if __name__ == "__main__":
    # bind to PORT so container healthchecks succeed
    app.run(host="0.0.0.0", port=PORT)
