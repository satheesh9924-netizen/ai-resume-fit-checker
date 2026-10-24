"""Tiny standard-library HTTP helper (no extra dependencies)."""
import base64
import json
import socket
import urllib.error
import urllib.request
from collections import namedtuple

Resp = namedtuple("Resp", "status body headers")


def request(method, url, headers=None, json_body=None, timeout=10.0):
    """Perform a request and return Resp without raising on 4xx/5xx. Timeouts propagate as TimeoutError."""
    data = None
    final_headers = dict(headers or {})
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=final_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return Resp(response.status, response.read().decode("utf-8"), _lower(response.headers))
    except urllib.error.HTTPError as error:
        return Resp(error.code, error.read().decode("utf-8"), _lower(error.headers))
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            raise TimeoutError(str(error.reason)) from error
        raise


def get(url, headers=None, timeout=10.0):
    return request("GET", url, headers, None, timeout)


def post(url, json_body=None, headers=None, timeout=10.0):
    return request("POST", url, headers, json_body, timeout)


def delete(url, headers=None, timeout=10.0):
    return request("DELETE", url, headers, None, timeout)


def basic_auth(user, password):
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def as_json(resp):
    return json.loads(resp.body) if resp.body else {}


def _lower(message_headers):
    return {key.lower(): value for key, value in message_headers.items()}
