import pytest

from env_lab import http
from env_lab.config import get_config
from env_lab.context import headers

pytestmark = pytest.mark.capability


@pytest.mark.requires("feature.bulk_import")
def test_bulk_import_is_accepted_where_enabled():
    resp = http.post(get_config().str("urls.orders") + "/orders/bulk", {"orders": []}, headers())
    assert resp.status == 202


@pytest.mark.min_version("5.0")
def test_dashboard_endpoint_exists_only_on_new_releases():
    resp = http.get(get_config().str("urls.orders") + "/dashboard", headers())
    assert resp.status == 200
