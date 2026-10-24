import pytest

from env_lab.config import EnvConfig, get_config, skip_reason

pytestmark = [pytest.mark.config, pytest.mark.offline]


def test_profile_resolves_to_a_consistent_target():
    cfg = get_config()
    assert cfg.str("expected.title"), "profile must define the expected page title"
    if cfg.deployment == "SINGLE_TENANT":
        assert not cfg.bool("capability.multi_tenant"), "a single-tenant target is never multi-tenant"
    else:
        assert cfg.bool("capability.multi_tenant"), "a SaaS target is multi-tenant"


def test_target_profile_overrides_deployment_defaults():
    # deployment-single_tenant says bulk_import = true; ACME's own profile switches it off
    acme = EnvConfig("onprem-acme", environ={})
    assert acme.bool("feature.bulk_import") is False
    assert EnvConfig("saas-tenant-a", environ={}).bool("feature.bulk_import") is True


def test_environment_variable_overrides_every_file_layer():
    cfg = EnvConfig("saas-tenant-a", environ={"LAB_URLS_WEB": "http://example.test"})
    assert cfg.str("urls.web") == "http://example.test"


def test_capability_gating_gives_a_reason():
    acme = EnvConfig("onprem-acme", environ={})
    assert "capability.multi_tenant" in skip_reason(acme, ["capability.multi_tenant"])
    assert "needs >= 5.0" in skip_reason(acme, [], "5.0")
    assert skip_reason(EnvConfig("saas-tenant-a", environ={}), ["capability.multi_tenant"], "5.0") is None
