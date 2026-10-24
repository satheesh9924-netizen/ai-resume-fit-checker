"""A small consumer-driven contract between Orders (consumer) and Payment (provider).

contracts/orders-payment.json is the contract: what Orders sends and what it needs back.
  * consumer side: the real PaymentClient is run against a tiny local server; we check it sends
    exactly what the contract says and can read the contract's response.
  * provider side: the contract's request is replayed against the running Payment service and the
    response must satisfy the contract.
This is the idea behind Pact, in about 100 lines. With Pact the contract file is published to a broker and
the Payment team's own pipeline runs the provider side, so a renamed field fails THEIR build.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from env_lab import http
from env_lab.payment_client import PaymentClient

CONTRACT = Path(__file__).resolve().parent.parent / "contracts" / "orders-payment.json"
PY_TYPES = {"string": str, "integer": int, "boolean": bool}

# What the Orders service actually does, owned by the CONSUMER (order id, amount in minor units, currency, idempotency key).
# The contract is compared against what the real client sends for this call; if the contract or the client
# drifts, the two disagree and the check fails.
CONSUMER_SCENARIO = ("1001", 2500, "INR", "key-1001")


def load_interaction(index=0):
    return json.loads(CONTRACT.read_text(encoding="utf-8"))["interactions"][index]


def run_consumer_check(interaction):
    """Return a list of problems (empty = the client honours the contract)."""
    expected = interaction["request"]
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            captured["method"] = "POST"
            captured["path"] = self.path
            captured["headers"] = {key.lower(): value for key, value in self.headers.items()}
            captured["body"] = json.loads(self.rfile.read(length) or b"{}")
            payload = json.dumps(interaction["response"]["example"]).encode("utf-8")
            self.send_response(interaction["response"]["status"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = PaymentClient(f"http://127.0.0.1:{server.server_port}", timeout=5.0)
        result = client.charge(*CONSUMER_SCENARIO)
    finally:
        server.shutdown()
        server.server_close()

    problems = []
    if captured.get("method") != expected["method"] or captured.get("path") != expected["path"]:
        problems.append(f"client called {captured.get('method')} {captured.get('path')}, "
                        f"contract says {expected['method']} {expected['path']}")
    for name, value in expected["headers"].items():
        if captured.get("headers", {}).get(name.lower()) != value:
            problems.append(f"header {name} was {captured.get('headers', {}).get(name.lower())!r}, contract says {value!r}")
    if captured.get("body") != expected["body"]:
        problems.append(f"body was {captured.get('body')}, contract says {expected['body']}")
    if result.status != interaction["response"]["example"]["status"]:
        problems.append(f"client could not read the contract's response (got status {result.status!r})")
    return problems


def verify_provider(base_url, interaction):
    """Replay the contract's request against the real Payment service. Return a list of problems."""
    expected = interaction["request"]
    resp = http.post(base_url + expected["path"], expected["body"], expected["headers"])
    problems = []
    if resp.status != interaction["response"]["status"]:
        problems.append(f"provider answered {resp.status}, contract says {interaction['response']['status']}")
        return problems
    payload = http.as_json(resp)
    for field, type_name in interaction["response"]["fields"].items():
        if field not in payload:
            problems.append(f"response is missing field '{field}'")
        elif not isinstance(payload[field], PY_TYPES[type_name]):
            problems.append(f"field '{field}' is not a {type_name}")
    return problems
