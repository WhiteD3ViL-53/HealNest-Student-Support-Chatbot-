#!/usr/bin/env python3
"""
proxy.py — reverse-proxy for two local Streamlit apps.

Routes:
- /        -> forwards to MAIN_TARGET (default http://127.0.0.1:8501)
- /admin   -> forwards to ADMIN_TARGET (default http://127.0.0.1:8502), with the /admin prefix removed
"""
import os
import requests
from flask import Flask, request, Response, stream_with_context
from urllib.parse import urljoin

app = Flask(__name__)

MAIN_TARGET = os.environ.get("MAIN_TARGET", "http://127.0.0.1:8501")
ADMIN_TARGET = os.environ.get("ADMIN_TARGET", "http://127.0.0.1:8502")
PORT = int(os.environ.get("PORT", 8080))


def _build_target_url(base, incoming_path):
    # incoming_path is request.full_path (path + ?query). We want to join base + path (no double slashes).
    if incoming_path.endswith("?"):
        incoming_path = incoming_path[:-1]
    # urljoin handles base + path correctly
    return urljoin(base, incoming_path.lstrip("/"))


def _proxy_request(target_base, strip_prefix=None):
    # Build the path to forward
    path = request.path  # path without query
    query = request.query_string.decode() if request.query_string else ""
    # Optionally strip a leading path prefix (e.g. "/admin")
    if strip_prefix and path.startswith(strip_prefix):
        forward_path = path[len(strip_prefix):]
        if not forward_path:
            forward_path = "/"  # ensure root
    else:
        forward_path = path

    # compose full forwarded path (path + query)
    forward_full = forward_path
    if query:
        forward_full = forward_full + "?" + query

    target_url = _build_target_url(target_base, forward_full)

    # copy headers except hop-by-hop and host
    excluded = {"host", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded}

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=None,               # already included in target_url
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


@app.route("/admin", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/admin/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_admin(path):
    # Strip the "/admin" prefix before forwarding
    return _proxy_request(ADMIN_TARGET, strip_prefix="/admin")


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_main(path):
    return _proxy_request(MAIN_TARGET, strip_prefix=None)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
