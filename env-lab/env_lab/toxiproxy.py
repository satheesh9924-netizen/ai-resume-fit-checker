"""Adds and removes network faults between the tests and the Payment service."""
from contextlib import contextmanager

from env_lab import http
from env_lab.config import get_config

TOXIC = "latency_downstream"


@contextmanager
def latency(millis):
    api = get_config().str("urls.toxiproxy")
    body = {"name": TOXIC, "type": "latency", "stream": "downstream",
            "toxicity": 1.0, "attributes": {"latency": millis, "jitter": 0}}
    resp = http.post(f"{api}/proxies/payment/toxics", body)
    if resp.status != 200:
        raise RuntimeError(f"Could not add latency toxic: {resp.status} {resp.body}")
    try:
        yield
    finally:
        http.delete(f"{api}/proxies/payment/toxics/{TOXIC}")
