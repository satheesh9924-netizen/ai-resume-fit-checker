import pytest

from env_lab import http
from env_lab.config import get_config
from env_lab.context import headers, new_correlation_id

pytestmark = [pytest.mark.tenant, pytest.mark.requires("capability.multi_tenant")]


def order_url(order_id):
    return f"{get_config().str('urls.orders')}/orders/{order_id}"


def test_tenant_can_read_its_own_order():
    cfg = get_config()
    resp = http.get(order_url(cfg.str("tenant.own_order_id")), headers())
    assert resp.status == 200
    assert http.as_json(resp)["tenant"] == cfg.str("tenant.id")


def test_tenant_cannot_read_another_tenants_order():
    cfg = get_config()
    resp = http.get(order_url(cfg.str("tenant.other_order_id")), headers())
    assert resp.status in (403, 404), f"expected 403/404 but got {resp.status}"
    assert "orderId" not in resp.body, "response must not leak the other tenant's record"


def test_request_without_tenant_is_rejected():
    cfg = get_config()
    resp = http.get(order_url(cfg.str("tenant.own_order_id")), headers(with_tenant=False))
    assert resp.status == 401


def test_correlation_id_comes_back_for_tracing():
    cfg = get_config()
    correlation_id = new_correlation_id()
    resp = http.get(order_url(cfg.str("tenant.own_order_id")), headers(correlation_id))
    assert resp.headers.get("x-correlation-id") == correlation_id
