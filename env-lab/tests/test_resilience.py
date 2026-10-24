"""'What happens when Payment is slow, down, or called twice?' Answered with real network faults."""
import time

import pytest

from env_lab import http, toxiproxy
from env_lab.config import get_config
from env_lab.payment_client import PaymentClient

pytestmark = pytest.mark.resilience


def test_payment_outage_surfaces_as_a_clean_error():
    resp = http.post(get_config().str("urls.payment") + "/payments/unavailable", {})
    assert resp.status == 503
    assert http.as_json(resp)["error"]


def test_slow_payment_is_cut_off_by_the_client_timeout_instead_of_hanging():
    with toxiproxy.latency(3000):
        client = PaymentClient(get_config().str("urls.payment_proxy"), timeout=1.0)
        start = time.monotonic()
        result = client.charge("1001", 2500, "INR", f"key-slow-{time.time_ns()}")
        elapsed = time.monotonic() - start

    assert result.status == "TIMEOUT"
    assert elapsed < 2.5, f"client should give up near its 1s timeout, took {elapsed:.1f}s"


def test_retry_with_the_same_idempotency_key_returns_the_same_payment():
    """Shape of an idempotency test: same key twice, same outcome.

    The stub always answers the same way, so this proves the TEST is wired correctly;
    against the real Payment service it proves 'no double charge'.
    """
    client = PaymentClient(get_config().str("urls.payment"))
    first = client.charge("1001", 2500, "INR", "key-1001")
    second = client.charge("1001", 2500, "INR", "key-1001")

    assert first.status == "CAPTURED"
    assert first.payment_id == second.payment_id
