# env-lab: one test suite, many environments

A small module that shows how a single automation suite is set up for different deployment
models. The tests are deliberately simple (a page title, a status code, a queue depth); the
environment around them is the point.

**Tests say what to verify. A profile says where and for whom. A Docker Compose overlay builds the where.**
Nothing in a test contains a URL, a credential or a tenant ID.

```
run_lab.sh <stack> <target>      one throw-away copy per run, own compose project and network
      |
      v
compose/base.yml            shared: payment (stub), toxiproxy (faults), rabbitmq (queue + DLQ), tests (runner)
 + compose/saas.yml         multi-tenant: ONE shared stack, tenant identified per request (X-Tenant-ID)
 + compose/onprem-acme.yml  single-tenant: one customer's own stack, older release, customised
      |
      v
profiles/*.ini  ->  env_lab/config.py (layered)  ->  tests/
```

## Environment types

| Environment | Stack | Target profile | What differs |
|---|---|---|---|
| Multi-tenant SaaS | `saas` | `saas-tenant-a`, `saas-tenant-b` | One shared stack; tenant travels in the `X-Tenant-ID` header; latest release (5.0) |
| Single-tenant on-prem | `onprem-acme` | `onprem-acme` | Own copy for one customer; older release (4.2); bulk import switched off; no DB access |
| Single-tenant cloud | `onprem-acme` | a new profile | Same overlay and behaviour as on-prem; only the profile values change |
| Ephemeral CI environment | any | any | Fresh containers and network per run, destroyed afterwards, so parallel builds do not collide |

## Profile layers (later wins)

1. `profiles/defaults.ini`
2. `profiles/deployment-<saas|single_tenant>.ini`: what is true of any target of that kind
3. `profiles/<target>.ini`: one concrete customer or tenant (selected with `LAB_TARGET`)
4. environment variables `LAB_<SECTION>_<KEY>`, for example `LAB_URLS_WEB`

Example: the single-tenant defaults enable bulk import; ACME's own profile turns it off, so
`test_bulk_import_is_accepted_where_enabled` is **skipped with a reason** on ACME and runs
everywhere else.

## Concept to file to test

| Concept | Where | Test |
|---|---|---|
| Layered config, env-var override, capability reasons | `env_lab/config.py`, `profiles/` | `test_config_layering.py` |
| Tenant context injected, never hard-coded | `env_lab/context.py` | `test_tenant_isolation.py` |
| Cross-tenant isolation (403/404 and no leak, 401 without a tenant) | `wiremock/orders-saas/` | `test_tenant_isolation.py` |
| Capability and version gating | `tests/conftest.py` (`requires`, `min_version` markers) | `test_capabilities.py` |
| Consumer-driven contract | `contracts/orders-payment.json`, `env_lab/contract.py` | `test_payment_contract.py` |
| Async without sleep, dead-letter queue | `rabbitmq/definitions.json`, `env_lab/waiting.py` | `test_async_dlq.py` |
| Failure and latency injection, timeouts | `toxiproxy/`, `env_lab/toxiproxy.py` | `test_resilience.py` |
| Idempotency (test shape) | `wiremock/payment/` | `test_resilience.py` |
| Correlation ID for tracing | `env_lab/context.py` | `test_tenant_isolation.py` |
| UI check, same test on any target | `tests/conftest.py` | `test_title_smoke.py` |

## Run it

Needs Docker with the Compose plugin (Colima is fine: `colima start`).

```bash
# the full suite against one target, in a fresh environment that is destroyed afterwards
bash env-lab/scripts/run_lab.sh saas saas-tenant-a
bash env-lab/scripts/run_lab.sh saas saas-tenant-b
bash env-lab/scripts/run_lab.sh onprem-acme onprem-acme

# only some tests (anything after the target goes to pytest)
bash env-lab/scripts/run_lab.sh onprem-acme onprem-acme -m "tenant or capability"
```

Without Docker, the tests marked `offline` still run anywhere:

```bash
cd env-lab && LAB_TARGET=onprem-acme pytest -m offline
```

On `onprem-acme` expect `test_tenant_isolation.py` skipped (not multi-tenant), and the bulk
import and dashboard tests skipped (customised off, and release 4.2 is older than 5.0).
Skipped with a reason is the design: a test is never silently dropped.

## What is real and what is a stand-in

- **Orders and Payment are WireMock stubs**, not real services. They give the suite something to
  run against; the setup, profiles, isolation checks and pipeline are the transferable part.
- **The dead-letter test** uses a message TTL with no consumer to force a dead-letter. It stands in
  for a poison message nobody could process.
- **The idempotency test** shows the shape of the check. A stub always answers the same way, so
  only the real Payment service proves "no double charge".
- **The contract check is a small hand-written version of the Pact idea.** Provider verification here
  replays the contract against the stub. In a real setup the contract is published to a broker
  (Pact) and the Payment team's own pipeline verifies it.
- **Not covered:** test data management, security scans, mobile.
