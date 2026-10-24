"""Async behaviour without sleep(): publish, then POLL for the outcome with a timeout.

Nobody consumes order.placed, so the message expires (TTL 1.5s) and is dead-lettered.
That stands in for a 'poison message nobody could process'.
"""
import pytest

from env_lab import http
from env_lab.config import get_config
from env_lab.waiting import wait_until

pytestmark = pytest.mark.messaging


def _api():
    cfg = get_config()
    return cfg.str("urls.rabbit") + "/api", http.basic_auth(cfg.str("rabbit.user"), cfg.str("rabbit.password"))


def test_dead_letter_routing_is_configured():
    api, auth = _api()
    resp = http.get(f"{api}/queues/%2F/order.placed", auth)
    assert resp.status == 200
    assert http.as_json(resp)["arguments"]["x-dead-letter-exchange"] == "dlx"


def test_unprocessed_message_ends_up_in_the_dead_letter_queue():
    api, auth = _api()
    http.delete(f"{api}/queues/%2F/order.placed.dlq/contents", auth)

    publish = {"properties": {}, "routing_key": "order.placed",
               "payload": "order-1001", "payload_encoding": "string"}
    resp = http.post(f"{api}/exchanges/%2F/amq.default/publish", publish, auth)
    assert resp.status == 200
    assert http.as_json(resp)["routed"] is True, "message was not routed to order.placed"

    def dlq_depth():
        queue = http.get(f"{api}/queues/%2F/order.placed.dlq", auth)
        return http.as_json(queue).get("messages", 0)

    wait_until(lambda: dlq_depth() >= 1, timeout=30, interval=1,
               message="dead-letter queue never received the message")
