---
name: claude-agent
description: >-
  Scaffold the TaskFlow black-box testing agent (an LLM agent that tests the
  TaskFlow to-do API against its shared contract). Use when the user says
  "create the testing agent", "build the TaskFlow QA agent", "scaffold the
  contract testing agent", or invokes /claude-agent. Builds a Python project
  with a bounded toolset, code-enforced guardrails, and both report formats.
---

# TaskFlow Testing Agent Builder

When this skill runs, build a contract-first, black-box QA agent for the
**TaskFlow** to-do API. TaskFlow is implemented three ways (same API contract
and data model), so the agent must test the running HTTP API — never the
implementation language or source — and work against any pod by changing only a
`base_url`.

If `references/taskflow-testing-agent.md` (or `taskflow-testing-agent.md` at the
repo root) exists, read it first and treat it as the authoritative spec. The
standards and methods below summarize it.

## Standards (non-negotiable)

- **Contract-first.** Every test derives from the loaded API contract, never
  from assumptions about how to-do apps "usually" behave. Ambiguities in the
  contract are reported as findings, not silently resolved.
- **Black-box.** The agent talks HTTP only. It does not read or run the app's
  source to decide pass/fail, and it never edits the application under test.
- **Guardrails enforced in code, not just prompt.** The HTTP tool physically
  rejects any host other than the configured `base_url`; retries happen only on
  connection errors, never on 4xx/5xx; a global request budget bounds the run.
- **Deterministic & isolated.** `temperature: 0`, seeded data, all test
  resources namespaced (`qa-agent-*`) and cleaned up even when a test fails.
- **Evidence-based reporting.** No failure is recorded without the exact request
  and the actual response that proves it.
- **Secrets hygiene.** The API key is read only from `ANTHROPIC_API_KEY`, never
  hardcoded, logged, or printed.

## Methods

**Operating loop the agent follows at runtime:**
1. LOAD — parse the contract; extract every endpoint, method, request/response
   schema, status code, and constraint.
2. HEALTH CHECK — confirm the target is reachable; stop and report if not.
3. PLAN — map each contract element to concrete test cases; list the plan first.
4. GENERATE — write a single pytest file (requests-based) into `tests_generated/`.
5. EXECUTE — run it via the test-runner tool.
6. TRIAGE — classify each failure (contract violation, validation gap,
   error-handling bug, data-integrity issue, or test-harness flaw); fix its own
   harness mistakes and rerun.
7. REPORT — emit JSON + Markdown per the schema below.

**Test taxonomy to cover:** contract conformance (status codes, response
schema, headers); CRUD happy paths; negative/validation (missing/typed/oversized
fields, malformed JSON → 400 not 500); error handling (404 unknown id, 405 bad
method, 404 unknown route, malformed id); data integrity/state (CRUD sequence
consistency, unique non-reused ids, list freshness, delete idempotency);
boundary (empty list → `[]`, unicode/emoji/whitespace titles). Assume a typical
model (`id`, `title`, `completed`, `created_at`) but override with the real
contract at runtime.

**Bounded toolset (give the agent exactly these):** `http_request` (base_url-
locked, timeout + retry + budget enforced), `run_tests` (pytest on
`tests_generated/` only), `read_contract` (read-only), `write_report`
(restricted to the report output dir), `read_file` (read-only, whitelisted).
Do NOT provide shell, package install, source editing, or DB admin.

## Build instructions

Use Python 3.11+, the `anthropic` SDK for the agent loop, `requests`, `pytest`,
and `pyyaml`. Produce this layout:

```
taskflow_agent/
  __main__.py            # CLI: python -m taskflow_agent --config <path>
  config.py              # load + validate the YAML config (fail fast)
  agent.py               # Anthropic tool-use loop
  prompts.py             # SYSTEM_PROMPT (encodes the operating loop above)
  tools/                 # http_request, run_tests, read_contract,
                         #   write_report, read_file — guardrails in code
  reporting.py           # build markdown + json reports
testing-agent.config.yaml  # sample config
mock_taskflow/app.py     # minimal in-memory Flask TaskFlow for smoke tests
tests_generated/         # agent writes its pytest file here
test-reports/            # agent writes reports here
README.md
requirements.txt
```

**Config schema** (`testing-agent.config.yaml`):
`target{base_url, contract_path, health_endpoint}`,
`run{timeout_seconds:10, max_retries:2, parallelism:1, data_namespace:"qa-agent",
seed:1337, max_requests:500}`,
`model{name:"claude-opus-4-8", temperature:0, max_tokens:4000}`,
`report{format:["markdown","json"], output_dir:"./test-reports", fail_fast:false}`.

**Report schema:** `{ target, contract_version, summary{total,passed,failed,
duration_s}, failures[{id,category,severity,request,expected,actual,repro}],
ambiguities[] }`. The run is GREEN only if the health check passes, all
contract-mapped tests pass, and no unhandled 500s occurred.

**Reference mock:** a minimal in-memory Flask TaskFlow (POST/GET/PUT/DELETE
`/tasks[/<id>]`, `GET /health`) so the agent is verifiable end-to-end before any
pod's implementation exists. It is a fixture, not a deliverable.

**Acceptance criteria — verify before finishing:**
1. `pip install -r requirements.txt` succeeds.
2. Against the running mock, the agent loads the contract, generates a pytest
   file, executes it, and writes `report.md` + `report.json`.
3. All agent-created resources are cleaned up afterward.
4. Demonstrate a guardrail: an `http_request` to a non-`base_url` host is
   rejected, and a 4xx is not retried.
5. No secrets printed; API key read only from the environment.

**Build order:** scaffold structure → implement config + tools + guardrails with
small unit tests → agent loop + reporting → run the full acceptance flow against
the mock and show the resulting report.
