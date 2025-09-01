# DTO — Cursor Development Prompt (Phase 0 → Phase 1 Scaffold)

**Use order:**  
1) Add **BRD/TDR v1.2** as context in Cursor.  
2) Then paste the following prompt **as the second prompt** to generate the scaffold.

---

## Prompt (paste everything below into Cursor)

You are an engineer implementing the “Data Testing Orchestrator (DTO)” exactly as defined in the attached **BRD/TDR v1.2**. 

**Hard rules**
- Do **not** invent tech or structure outside BRD/TDR v1.2.  
- Produce a **working monorepo scaffold** with stubs and tests (no full features yet).  
- Enforce **determinism**, **SELECT-only guardrails**, **JSON Schema validation**, and security defaults.  
- Prefer readability and clear boundaries over completeness at this phase.

---

### Deliverables (Phase 0–1 Scaffold)

**1) Monorepo layout**
```
/
├─ backend/                    # FastAPI + Typer
│  ├─ dto_api/                 # FastAPI app
│  │  ├─ main.py
│  │  ├─ routers/ (v1 endpoints: catalog, datasets, tests, runs, settings, health)
│  │  ├─ models/  (Pydantic v2: CatalogPackage, TestDef, IR, ReportRecord)
│  │  ├─ services/ (catalog_import, planner, runner_stub, ai_adapter_iface)
│  │  ├─ adapters/
│  │  │  ├─ connectors/ (snowflake_stub.py, postgres_stub.py)
│  │  │  ├─ auth/ (oidc_stub.py, iam_stub.py, kerberos_stub.py, mtls_stub.py, vault_stub.py)
│  │  │  └─ storage/ (artifacts_s3_stub.py, local_fs.py)
│  │  ├─ policies/ (pii_redaction.py, sql_preview_off.py)
│  │  ├─ schemas/  (jsonschema files for AI I/O validation)
│  │  └─ telemetry/ (logging.py, metrics.py)
│  ├─ dto_cli/ (Typer: run, propose, compile, import-catalog, health)
│  ├─ tests/ (pytest: contract tests for API/CLI; golden samples)
│  ├─ pyproject.toml, alembic/, README.md
│  └─ Dockerfile
├─ frontend/                   # Next.js 14 + TS + Tailwind + shadcn/ui
│  ├─ app/
│  │  ├─ (routes) /runs /suites /datasets /builder /settings
│  │  ├─ components/ (Cards: schema/integrity/reconciliation/freshness/rule/drift)
│  │  ├─ lib/ (api client via fetch, zod validators, tanstack query setup)
│  │  └─ store/ (zustand)
│  ├─ styles/, tailwind.config, next.config, package.json
│  └─ Dockerfile
├─ infra/
│  ├─ docker-compose.yml (api, ui, postgres, minio)
│  ├─ helm/ (skeleton chart values.yaml with policies defaults)
│  └─ terraform/ (examples only; no cloud creds)
├─ artifacts/ (gitignored)
├─ docs/ (BRD copy + API spec openapi.json generated)
├─ .github/workflows/ (lint+type+test; build images; SBOM)
├─ LICENSE (Apache-2.0)
└─ README.md (dev quickstart)
```

**2) Backend scope (stubs only, runnable)**
- FastAPI `/api/v1` endpoints:
  - `GET /healthz`, `GET /readyz`, `GET /version`
  - `POST /catalog/import` (accept Catalog Package JSON or dbt manifest/catalog; persist to Postgres)
  - `GET /catalog/{id}`, `GET /catalog/{id}/diff/{prev}`
  - `POST /tests/propose` (returns mock proposals from `ai_adapter_iface`; validate with JSON Schema)
  - `POST /tests/compile` (NL/Formula → IR stub; return `sql_preview` echo; no execution)
  - `POST /suites/{id}/run` (runner_stub returns a fake `run_id`, writes HTML+JSONL placeholders)
  - `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/results`, `GET /runs/{id}/artifacts`
  - `GET/POST /settings/*` (connection/auth/ai/policy settings)
- Typer CLI mirrors API (run, propose, compile, import-catalog).
- SQLAlchemy + Alembic (Postgres run store).
- **Policies default:** external AI OFF, SQL preview OFF, PII redaction ON.
- **Observability:** JSON logs, request IDs; Prometheus metrics endpoint.
- **Tests:** API contract tests, JSON Schema validation tests (pytest).

**3) Frontend scope (wireframes + mock data)**  
- Pages: Home/Run History, Test Builder (Zero-SQL cards), Datasets & Catalog (schema/diff), Run Details (Failure Explainer placeholder), Settings.  
- Forms: `react-hook-form` + `zod`; tables: TanStack Table; charts: Recharts; Monaco for YAML/JSON views.  
- Mock API layer switchable to real backend via env.  
- Dark/light theme; keyboard shortcuts; “Copy as YAML” for test defs.

**4) Security & Guardrails in code**
- SELECT-only: adapters reject DDL/DML even as stubs.
- EXPLAIN preflight hook placeholder.
- PII redaction stub in AI context packer.
- Configurable scan/time budgets (config present, no-op at stub level).

**5) Dev UX**
- `docker compose up` → API `:8000`, UI `:3000`, Postgres + MinIO.  
- Makefile: `make dev`, `make fmt`, `make test`, `make openapi`.  
- Pre-commit: ruff/black/mypy (backend) + eslint/prettier (frontend).

**6) Documentation**
- Autogenerate OpenAPI json into `docs/`.  
- README quickstart with env vars, compose, sample curl.

---

### Acceptance for this phase
- `docker compose up` brings **API/UI** with green health endpoints.  
- API routes exist and validate payloads per **JSON Schemas**.  
- CLI generates placeholder **HTML/JSONL** artifacts for a fake run.  
- Frontend navigable with mocked data; **Test Builder** shows dynamic cards.  
- CI workflow executes lint, type-checks, and tests.

---

### Next prompt to follow (Phase 1.5 plan)
After the scaffold is generated, I will provide a follow-up prompt to implement:
- real Snowflake/Postgres connectors (read-only)
- minimal runner with EXPLAIN pre-check + SELECT execution
- AI adapter integration (local LLM stub)
- Catalog diff logic
- basic SEP contract validations
