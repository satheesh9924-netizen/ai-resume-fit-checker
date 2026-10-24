"""The 'tenant context' layer: tests never build tenant headers themselves.

On a multi-tenant target every call carries X-Tenant-ID; on a single-tenant target it does not.
Every call carries a correlation ID so a failed request can be found in the service logs.
"""
import os
import uuid

from env_lab.config import get_config


def new_correlation_id():
    return f"lab-{os.environ.get('BUILD_NUMBER', 'local')}-{uuid.uuid4().hex[:8]}"


def headers(correlation_id=None, with_tenant=True):
    cfg = get_config()
    result = {"X-Correlation-Id": correlation_id or new_correlation_id()}
    if with_tenant and cfg.bool("capability.multi_tenant"):
        result["X-Tenant-ID"] = cfg.str("tenant.id")
    return result
