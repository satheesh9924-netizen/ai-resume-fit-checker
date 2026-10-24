import pytest

from env_lab.config import get_config
from env_lab.contract import load_interaction, run_consumer_check, verify_provider

pytestmark = pytest.mark.contract


@pytest.mark.offline
def test_orders_client_sends_exactly_what_the_contract_says():
    """Consumer side: needs no environment, so it can gate a build before anything is deployed."""
    assert run_consumer_check(load_interaction()) == []


def test_payment_service_honours_the_contract():
    """Provider side: replay the contract against the running Payment service."""
    assert verify_provider(get_config().str("urls.payment"), load_interaction()) == []
