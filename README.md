AI-Augmented Test Automation Platform (Personal Project)

- Architected an end-to-end test automation pipeline using Playwright (Java) + TestNG, containerized with Docker/Docker Compose, and orchestrated by a self-hosted Jenkins CI/CD pipeline with automatic SCM-triggered builds (poll + webhook), eliminating manual test execution.
- Designed a 5-stage declarative Jenkins pipeline (Docker environment validation, containerized test execution, AI evaluation suites, AI failure triage, unified reporting) with credential-scoped secrets management via Jenkins Credentials store — zero secrets committed to source control.
- Built a structured LLM-output reliability layer around Claude API calls (via an OpenAI-compatible gateway): defensive JSON extraction/parsing, retry-on-malformed-output logic, and Jackson version-conflict resolution across a multi-module Maven build.
- Engineered an AI-powered resume-to-job-description matching service (Claude Sonnet) with a 5-category automated evaluation suite covering schema validation, golden-set accuracy regression, groundedness/hallucination detection (keyword-overlap grounding checks), prompt-injection adversarial testing, and demographic bias/fairness testing — directly addressing known production risks in AI-driven hiring tools.
- Built an AI CI-failure triage bot (Claude Haiku) that parses Surefire/JUnit XML reports and auto-classifies failures (flaky / regression / environment) with root-cause summaries, reducing manual failure-triage overhead.
- Implemented unified Allure test reporting aggregated across 3 independent Maven modules into a single dashboard, integrated into Jenkins with screenshot/trace capture on failure for debuggability.
- Debugged and resolved production-grade integration issues independently: Docker bind-mount/mvn clean conflicts, transitive dependency (Jackson) version mismatches, Jenkins process environment (PATH) isolation, and LLM output non-determinism (malformed JSON, prompt-injection resistance, golden-set calibration).

Tech Stack: Java 17 · Maven · Playwright · TestNG · Docker · Docker Compose · Jenkins (Pipeline-as-Code) · Allure · Claude API (Anthropic, via OpenAI-compatible gateway) · Jackson · Git/GitHub · Colima

AI/LLM Testing Techniques Applied: golden-set regression testing, LLM-output groundedness/hallucination checks, adversarial prompt-injection testing, bias & fairness testing, structured-output schema validation, retry-based reliability patterns for non-deterministic outputs



# playwright-java-jenkins

End-to-end test automation pipeline: Playwright (Python) + pytest, containerized with Docker,
run by a local Jenkins instance, reported with Allure -- plus two Claude-powered testing
modules (resume/JD matcher with a full AI-eval test suite, and an AI CI-failure triage bot).

Repo: https://github.com/satheesh9924-netizen/playwright-java-jenkins

> Originally built in Java (Playwright Java + TestNG + Maven); ported to Python
> (Playwright Python + pytest + pip) on the `python-migration` branch. The repo name is a
> holdover from that history.

## Repo layout

Three independent Python projects, each with its own `requirements.txt`, `pytest.ini`, and `Dockerfile`:

```
.
├── tests/                  # e2e Playwright/pytest tests (root module)
├── resume-matcher/         # Resume-vs-JD fit matcher + AI-eval test suite
├── ai-triage/              # AI CI-failure triage bot (classifies FLAKY/REGRESSION/ENVIRONMENT)
├── Dockerfile               # root module image (mcr.microsoft.com/playwright/python)
├── docker-compose.yml       # all 4 services: e2e tests + both AI modules
├── Jenkinsfile               # 4-stage pipeline, see below
└── pytest.ini
```

## Local infrastructure

Everything runs locally on this Mac as persistent background services (`brew services`):

| Service | How it runs | Notes |
|---|---|---|
| **Colima** | `brew services start colima` | Lightweight VM providing the Docker daemon. `docker` / `docker compose` talk to it via the `colima` context. Note: Colima only shares the home directory tree into the VM -- bind mounts must live under a shared path (e.g. this repo); `/tmp` is **not** shared, so scratch files there are invisible inside containers. |
| **Jenkins LTS** | `brew services start jenkins-lts` | Bound to `127.0.0.1:8080` only (not exposed on the network). `JENKINS_HOME` is `~/.jenkins`. |

**Jenkins login:** `admin` / (password was generated at setup time -- not stored in this repo;
if lost, reset via `~/.jenkins/init.groovy.d/basic-security.groovy` and restart the service, or
use the Jenkins script console).

**Jenkins plugins installed:** `git`, `workflow-aggregator` (Pipeline), `github`,
`allure-jenkins-plugin` (+ its `matrix-project` dependency -- required or the Allure publisher's
extensions silently fail to register).

**Global Jenkins config (survives `brew services restart`, stored in Jenkins' own config, not
the launchd plist):**
- `PATH+HOMEBREW` env var = `/opt/homebrew/bin:/opt/homebrew/sbin` (otherwise Jenkins can't find `docker`)
- Allure Commandline tool installation named `allure`, auto-installs v2.30.0

**Jenkins credentials:**
- `abacus-api-key` (Secret Text) -- the Abacus RouteLLM API key, injected into the AI stages via `withCredentials`

## Pipeline stages (Jenkinsfile)

Triggers: `pollSCM('H/2 * * * *')` (checks GitHub every ~2 min -- this Jenkins isn't publicly
reachable, so the `githubPush()` webhook trigger is registered but dormant) and `githubPush()`
(ready if Jenkins is ever exposed publicly).

1. **Checkout**
2. **Verify Docker Environment** -- fails fast with a clear message if `docker`/`docker compose` aren't reachable
3. **Build & Run Tests (Docker)** -- builds the root image, runs the Playwright/pytest e2e suite
4. **Resume/JD Matcher AI Tests** -- builds & runs `resume-matcher`'s test suite (needs `ABACUS_API_KEY`)
5. **AI Failure Triage** -- runs `ai-triage`'s own test suite, then runs the triage bot itself against `target/surefire-reports` from stage 3, writing `ai-triage/target/triage-report.md`

`post.always`: fixes any root-owned files Docker wrote into the three `target/` dirs, tears
down containers/networks, publishes JUnit results, archives artifacts (screenshots, traces,
surefire reports, the triage markdown report), publishes the Allure report.

## Running locally without Docker

```
pip install -r requirements.txt && playwright install --with-deps chromium && pytest
pip install -r resume-matcher/requirements.txt && (cd resume-matcher && pytest)   # needs ABACUS_API_KEY
pip install -r ai-triage/requirements.txt && (cd ai-triage && pytest)            # needs ABACUS_API_KEY
```

## The AI modules

Both call Claude through **Abacus.AI's RouteLLM** (`https://routellm.abacus.ai/v1`), an
OpenAI-compatible gateway -- not Anthropic's native API directly. That's why the code uses the
`openai` Python SDK (pointed at a custom `base_url`) rather than `anthropic`.
Auth: `ABACUS_API_KEY` env var (mapped from the Jenkins credential in CI; export it locally to
run the modules yourself).

### `resume-matcher`

Takes a resume + job description, returns a structured match verdict (`match_score`, `verdict`,
`matched_skills`, `missing_skills`, `reasoning`). Model: `claude-sonnet-5`.

The test suite (`tests/test_*.py`) demonstrates the core AI-testing concepts:

| Test module | Concept |
|---|---|
| `test_schema_validation.py` | Output structure is valid independent of whether the verdict is "right" |
| `test_accuracy_golden_set.py` | Golden-set regression: hand-labeled (resume, JD) pairs with an expected **score range**, not an exact value -- rerun whenever the prompt changes |
| `test_groundedness.py` | Claimed skills must share real keyword overlap with the source text (not exact-phrase match -- too brittle for paraphrasing) |
| `test_prompt_injection.py` | A fixture resume embeds a fake "system override" claiming a perfect score -- asserts it's ignored |
| `test_bias_fairness.py` | Two resumes, identical qualifications, differing only in name/grad-year -- asserts scores stay within tolerance |

Golden fixtures live in `resume-matcher/tests/golden/` (all synthetic, no real PII).

### `ai-triage`

Parses `TEST-*.xml` JUnit reports (pytest's `--junitxml` output), classifies each failure
(`FLAKY` / `REGRESSION` / `ENVIRONMENT` / `UNKNOWN`) with a summary + suggested action. Model:
`claude-haiku-4-5` (cheap classification task, run frequently in CI). `test_triage_accuracy.py`
is its own golden-set suite (synthetic timeout/selector-break/docker-daemon-down fixtures).

Run standalone: `python -m ai_triage.failure_triage <surefire-reports-dir> <output.md>`

## Real issues hit while building this (worth knowing if things break)

- **LLM JSON output isn't 100% reliable**, even under an explicit "respond with ONLY a JSON
  object" instruction: seen in practice -- responses wrapped in ` ```json ` fences, duplicate
  JSON keys, stray trailing punctuation, outright malformed syntax mid-object. Both
  `ResumeMatcher` and `FailureTriage` defensively extract the `{...}` span and parse it with
  `json.loads` (which, like Jackson's tree model, takes the last value on duplicate keys rather
  than raising), retrying up to 3x on parse failure.
- **`allure.attachment_type` has no `ZIP` member** -- discovered when wiring up trace-on-failure
  attachments (`tests/conftest.py`). Pass `extension="zip"` to `allure.attach.file(...)` instead
  of guessing at an enum value; `dir(allure.attachment_type)` is the fastest way to check what
  actually exists in a given `allure-pytest` version.
- **pytest auto-collects any class named `Test*`** -- the domain type `ai_triage.models.TestFailure`
  (ported straight from the Java `record TestFailure`) collided with this and produced a
  `PytestCollectionWarning`. Fixed with a `__test__ = False` class attribute rather than renaming
  the type, since the name is otherwise a correct and meaningful one.
- **Colima doesn't share `/tmp` into the Docker VM** -- a bind mount rooted at `/tmp/...` is
  silently empty inside the container (no error, `os.listdir` just returns `[]`). Bind mounts
  need to live under a path Colima actually shares (e.g. the repo itself, or elsewhere under
  the home directory).
- **Golden-set tolerances need calibration**, especially for deliberately ambiguous cases
  (`case3_partial_fit` needed a wider range than the clear-cut strong/no-fit cases).
