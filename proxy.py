# proxy.py — reverse-proxy for / -> mental(8501), /admin -> Admin(8502)
import os
import requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

MAIN_TARGET = os.environ.get("MAIN_TARGET", "http://127.0.0.1:8501")
ADMIN_TARGET = os.environ.get("ADMIN_TARGET", "http://127.0.0.1:8502")
PORT = int(os.environ.get("PORT", 8080))

# Helper to forward a request and stream the response back
def _proxy_request(target_base):
    # request.full_path contains query string; remove trailing '?' if none
    path = request.full_path
    if path.endswith('?'):
        path = path[:-1]
    target_url = target_base + path

    # copy headers except hop-by-hop & host/length
    excluded_headers = ("host", "content-length", "transfer-encoding", "connection")
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_headers}

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            stream=True,
            timeout=30
        )
    except Exception as e:
        return Response(f"Upstream request failed: {e}", status=502)

    excluded_resp = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded_resp]

    return Response(stream_with_context(resp.iter_content(chunk_size=8192)),
                    status=resp.status_code, headers=resp_headers)

@app.route("/admin", defaults={"path": ""}, methods=["GET","POST","OPTIONS","PUT","DELETE","PATCH"])
@app.route("/admin/<path:path>", methods=["GET","POST","OPTIONS","PUT","DELETE","PATCH"])
def proxy_admin(path):
    return _proxy_request(ADMIN_TARGET)

@app.route("/", defaults={"path": ""}, methods=["GET","POST","OPTIONS","PUT","DELETE","PATCH"])
@app.route("/<path:path>", methods=["GET","POST","OPTIONS","PUT","DELETE","PATCH"])
def proxy_main(path):
    return _proxy_request(MAIN_TARGET)

if __name__ == "__main__":
    # bind to PORT so Cloud/Render healthchecks succeed
    app.run(host="0.0.0.0", port=PORT)
