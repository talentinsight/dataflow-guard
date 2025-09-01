# Data Testing Orchestrator (DTO) — BRD/TDR v1.2 (Markdown)

**Status:** Finalized draft for implementation context (Cursor‑ready)  
**Date:** 2025‑08‑31  
**Owner:** Data Testing Orchestrator (separate from LLM project)  
**Audience:** Data QA / Data Engineers / Platform / Security / UI

> **What’s new in v1.2 (compared to v1.1):**
> - Clarified **Test Data Requirements** by operating mode (In‑Network vs Air‑Gapped) and introduced **Source Evidence Package (SEP)**.  
> - Specified **accepted upload formats** (Parquet/Arrow/CSV + schema companion) and a **recommended folder layout**.  
> - Added a full section on **RAW JSON/VARIANT** testing (nested arrays, flatten cardinality, path/type assertions).  
> - Defined **Test Planning & Selection**: auto‑proposed test packs, scope filters, **Smoke/Standard/Deep/Custom** profiles, budget/impact‑based planning.  
> - Documented **Minimum Inputs** (table names, grain/keys, watermark, transform logic via dbt/TxSpec).  
> - Minor policy clarifications: **SQL preview off by default**, optional **Admin Power Mode** (read‑only, guarded).

---

## 0) Executive Summary

DTO is a **Zero‑SQL, AI‑assisted, push‑down** data‑testing framework. Engineers define tests via **dynamic UI cards** or simple **NL/Formula DSL**; an **AI compiler** turns intent into **read‑only, dialect‑aware SQL**. Tests run **in‑network** against customer databases (or **air‑gapped** on Parquet snapshots). Results are standardized (HTML + JSONL), CI‑gated, and auditable.

---

## 1) Scope & Goals

### 1.1 In‑Scope (MVP)
- Metadata ingestion (DB introspection **or** air‑gapped Catalog Package import)
- Zero‑SQL Test Builder (dynamic cards) + AI Compiler (NL/Formula → IR → SQL)
- Core test families: **Schema/Contract, Integrity (PK/FK/Not‑Null), Reconciliation (rowcount/aggregates), Freshness, Business Rules, basic Drift**
- Deterministic Runner (CLI & API), artifacted **HTML/JSONL** reports
- Auth without long‑lived secrets: **IAM/OIDC/Kerberos/mTLS/Vault**
- Optional imports: **dbt Core** manifest/catalog, Glue/Metastore; optional **OpenLineage** emit

### 1.2 Out‑of‑Scope (MVP)
- Full governance catalog, heavy masking pipelines, complex streaming tests (planned next phases)

### 1.3 Success Criteria (initial targets)
- **Zero‑SQL coverage:** ≥ **95%** of production tests authored without SQL
- **T0FF:** ≤ **5 min** from catalog import/connection to running first 5 tests
- **Performance:** Typical suite (≤30 tests on large tables) finishes **< 15 min** with push‑down; auto‑sampling if over budget
- **Determinism:** Identical inputs (catalog + tests + seed) ⇒ identical outputs (± timestamps)
- **Security:** All queries **SELECT‑only**; PII redaction on; static long‑lived secrets **discouraged/blocked by policy**

---

## 2) Operating Modes

1) **In‑Network (recommended):** Runner inside customer VPC/on‑prem, DB via read‑only role; no public egress required.  
2) **Air‑Gapped:** Tests run on **file snapshots** (Parquet/CSV) + **Catalog Package** (metadata JSON).  
3) **Hybrid:** Read‑replica/secure views or a **query proxy**; or push computations to a warehouse that mirrors prod.

---

## 3) Personas & Interfaces

- **Primary:** Data Engineer / Data QA → **CLI & API** (non‑interactive), headless CI.  
- **Secondary:** BI/Steward → **Web UI** (review runs, approve test proposals, triage).  
- **Platform/SRE:** Deploy/operate (K8s), secrets, RBAC, policies, monitoring.

**Interface priority:** CLI/API first, **but** UI is required and fully functional for Zero‑SQL authoring.

---

## 4) Technology Decisions (Finalized)

### 4.1 Backend (API + Runner)
- **Language:** Python **3.11+**
- **Web Framework:** **FastAPI** (ASGI)
- **Server:** **Uvicorn** (dev), **Gunicorn+Uvicorn workers** (prod)
- **CLI:** **Typer**
- **Data Access:** **SQLAlchemy 2.x** (core) + vendor drivers (psycopg / snowflake‑connector / pyodbc as needed)
- **Migrations:** **Alembic**
- **Validation:** **Pydantic v2**
- **Serialization:** orjson / stdlib json
- **Background Jobs (optional):**  
  - Default: **in‑process worker** (asyncio + ProcessPoolExecutor)  
  - Scalable option: **RQ (Redis Queue)** or **Celery** (pluggable)  
- **File/Snapshot Engine:** **PyArrow** + **DuckDB** (Parquet/CSV push‑down in air‑gapped mode)
- **Auth Providers (pluggable):** **OIDC/SAML SSO**, **AWS IAM/STS**, **Kerberos/GSSAPI**, **mTLS key‑pair**, **Vault dynamic creds**, static secret (discouraged)
- **Secrets:** **HashiCorp Vault** (preferred) or **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager**
- **Run Store (DB):** **Postgres 15+** (default), **SQLite** for dev
- **Artifacts:** **S3‑compatible** storage (AWS S3/MinIO/GCS/Azure Blob), local disk for dev
- **Observability:**  
  - Logs: **JSON‑structured** (uvicorn/access + app), request IDs  
  - Metrics: **Prometheus** (via **prometheus‑fastapi‑instrumentator**)  
  - Tracing (optional): **OpenTelemetry** exporters
- **Packaging/Deploy:** **Docker** (multi‑stage), **Helm** charts (K8s), **Terraform** examples
- **Testing:** **pytest**, **pytest‑xdist**, **mypy**, **ruff/black**; contract tests for adapters

### 4.2 AI Service (Adapter Layer)
- **Role:** Compile **NL/Formula → IR → SQL**, propose tests, explain failures
- **Providers:** **Local LLM (vLLM/Ollama)** preferred; optional **Azure OpenAI / Vertex AI / OpenAI**  
- **Determinism:** `temperature=0`, `top_p=1`, `seed` fixed; outputs validated with **JSON Schema**
- **Safety/Privacy:** **SELECT‑only**, PII redaction in context packer; prompts/artifacts **immutable** logged
- **Transport:** gRPC or HTTP (simple REST), **provider adapters** behind a single interface

### 4.3 Frontend (Web UI)
- **Framework:** **Next.js 14+ (App Router)**, **TypeScript 5+**
- **Styling/UI:** **TailwindCSS**, **shadcn/ui**
- **State/Data:** **TanStack Query v5** (server state), **Zustand** (local UI state)
- **Forms/Validation:** **React Hook Form** + **Zod**
- **Tables:** **TanStack Table v8**
- **Charts:** **Recharts**
- **Code/YAML Viewer:** **Monaco Editor**
- **Auth:** **Auth.js (NextAuth)** with **OIDC** provider; session cookies (HTTP‑only), CSRF enabled
- **Build/Bundle:** Vercel SWC/Next build; self‑hosted on K8s in prod
- **Accessibility/UX:** Keyboard‑first, ARIA, dark mode, low‑latency optimistic updates

### 4.4 Integrations (OSS‑First)
- **dbt Core (OSS):** ingest `manifest.json` + `catalog.json` (optional)  
- **OpenLineage (OSS):** emit lineage events (optional)  
- **Airflow:** lightweight Operator to call CLI (optional)  
- **Glue/Metastore/BigQuery Info Schema:** catalog import adapters

---

## 5) Test Data Requirements & Upload Formats (NEW)

### 5.1 In‑Network mode (DB connected)
- **No test‑data upload is required.**  
- Tests run push‑down on the source DB/DWH.  
- **Minimum inputs:** connection/auth, and if policies disallow live introspection, a **Catalog Package** (metadata‑only JSON).

### 5.2 Air‑Gapped mode (no DB connection)
**Required uploads:**
1) **Catalog Package (`catalog.json`)** — schema/PK‑FK/watermark/lineage (no rows).  
2) **Dataset snapshots** (each table/view to be tested): **Parquet (preferred)**; Arrow/Feather acceptable; CSV allowed **with schema companion**.

**Optional uploads:**
- **Lookups / enums** (CSV/JSON).  
- **Baseline stats** for drift thresholds (JSON).  
- **Previous snapshot** (for SCD/interval checks).

**Formats (accepted):**
- **Parquet** (recommended; partitioned by date/batch if possible)  
- **Arrow/Feather** (small/medium data)  
- **CSV + schema companion (`schema.yaml` or `schema.json`)**

**Recommended folder layout:**
```
upload/
  catalog/
    catalog.json
  data/
    RAW.ORDERS/
      snapshot_date=2025-08-30/part-000.parquet
    PREP.ORDERS/
      snapshot_date=2025-08-30/part-000.parquet
  lookups/
    order_statuses.csv
  stats/
    baseline_profile.json        # optional
  README.md
```

**CSV schema companion (minimal example):**
```yaml
dataset: RAW.ORDERS
columns:
  - { name: ORDER_ID, type: NUMBER, nullable: false }
  - { name: ORDER_TS, type: TIMESTAMP, nullable: false }
  - { name: ORDER_TOTAL, type: NUMBER, nullable: false }
```

### 5.3 Source→RAW reconciliation without source access (NEW)
Provide a lightweight **Source Evidence Package (SEP)** instead of raw source data:

- `source_contract.json` — keys, required fields/paths, type hints.  
- `batch_manifest.json` — `{ batch_id, window:[t1,t2), expected_rowcount, control_totals:{ SUM(amount), DISTINCT(key), MIN/MAX(ts) }, checksums }`.  
- `sample_keys.parquet` (optional) — masked 1–2K IDs for spot‑checks (no row data).

DTO computes the same metrics on RAW (same window/batch) and **reconciles** with SEP using configured tolerances.

---

## 6) Core Domain & Data Contracts

### 6.1 Catalog Package (authoritative metadata for builders)
```json
{
  "version": "1.0",
  "generated_at": "ISO-8601",
  "environment": "dev|stage|prod",
  "datasets": [
    {
      "name": "RAW.ORDERS",
      "kind": "table|view",
      "row_count_estimate": 123456,
      "columns": [
        {"name":"ORDER_ID","type":"NUMBER","nullable":false},
        {"name":"ORDER_TS","type":"TIMESTAMP_NTZ","nullable":false}
      ],
      "primary_key": ["ORDER_ID"],
      "foreign_keys": [{"columns":["CUSTOMER_ID"],"ref":"DIM.CUSTOMER(CUSTOMER_ID)"}],
      "watermark_column": "ORDER_TS",
      "lineage": ["SRC.ORDERS_RAW"]
    }
  ],
  "signatures": {"RAW.ORDERS": "sha256-of-column-list"}
}
```

### 6.2 Test Definition (Zero‑SQL card → stored YAML)
```yaml
suite: "orders_basic"
connection: "snowflake_prod"
tests:
  - name: "pk_uniqueness_orders"
    type: "uniqueness"
    dataset: "RAW.ORDERS"
    keys: ["ORDER_ID"]
    tolerance: { dup_rows: 0 }
    severity: "blocker"
    gate: "fail"
  - name: "business_rule_total_consistency"
    type: "rule"
    expression: "order_total == items_total + tax + shipping"
    dataset: "PREP.ORDERS"
    window: { last_days: 30 }
    filter: { returns: "none" }
    tolerance: { abs: 0.01 }
    severity: "major"
    gate: "fail"
```

### 6.3 IR/AST (AI compiler contract, output excerpt)
```json
{
  "ir_version": "1.0",
  "dataset": "PREP.ORDERS",
  "filters": [{"type":"time_window","column":"ORDER_TS","last_days":30},
              {"type":"equals","column":"RETURN_FLAG","value":"N"}],
  "joins": [{"left":"PREP.ORDERS.CUSTOMER_ID","right":"DIM.CUSTOMER.CUSTOMER_ID","type":"left"}],
  "aggregations": [],
  "assertion": {"kind":"equality_with_tolerance",
                "left":"ORDER_TOTAL",
                "right":{"expr":"ITEMS_TOTAL + TAX + SHIPPING"},
                "tolerance":{"abs":0.01}},
  "partition_by": [],
  "dialect": "snowflake"
}
```

### 6.4 Report Record (JSONL line per result)
```json
{
  "run_id":"2025-08-31T13:45:00Z-abc123",
  "suite":"orders_basic",
  "test":"business_rule_total_consistency",
  "status":"fail|pass|error",
  "metrics":{"violations":7,"sample_rows_uri":"artifact://runs/abc123/samples/..."},
  "started_at":"ISO-8601","ended_at":"ISO-8601",
  "ai":{"model":"local-llm:Q4_K_M","seed":42,"temperature":0,"top_p":1,
        "prompts_uri":"artifact://runs/abc123/ai/prompts.jsonl"}
}
```

---

## 7) RAW JSON/VARIANT Testing (NEW)

When RAW contains a single **VARIANT/JSON** column (or ARRAY of OBJECTs), DTO treats semi‑structured flows as first‑class:

- **JSON validity:** all `payload` rows are parseable; rejects counted & reported.  
- **Path existence:** required JSON paths exist, e.g. `$.id`, `$.event_ts`, `$.items`.  
- **Type checks & enums:** `$.amount` is number; `$.status` ∈ allowed set; `$.event_ts` is a valid timestamp.  
- **Schema versioning:** `$.schema_version ∈ {v1,v2}` (unknown versions warned/failed).  
- **Uniqueness:** `$.id` uniqueness (dedupe/incremental idempotency).  
- **Freshness/late arrivals:** `MAX($.event_ts)` lag ≤ SLA; late arrival rate tracked.  
- **Flatten cardinality:** `SUM(array_length($.items))` equals row‑count in `FACT_ITEMS` (same window/batch).  
- **Mapping equivalence:** PREP columns match source JSON paths (e.g., `PREP.order_total == $.totals.order_total`).  
- **FK integrity (child→parent):** `FACT_ITEMS.parent_id` → `FACT_ORDERS.id` coverage.  
- **Drift:** key presence, type drift, array length distribution changes flagged.

**UI support:** JSON Explorer & Path Picker, dynamic cards (path/type/enum/flatten/mapping/FK), AI compiler generates dialect‑aware SQL (Snowflake `LATERAL FLATTEN`, BigQuery `UNNEST`, Postgres `jsonb_*`).

---

## 8) Test Planning & Selection (NEW)

DTO uses **auto‑discovery → proposal → approval**:

- **Auto‑proposed packs** by layer:  
  - *Source→RAW:* manifest/SEP reconciliation (rowcount & control totals), JSON parse/path exists, freshness, duplicate/idempotency.  
  - *RAW→PREP:* schema/nullable, PK/FK, flatten cardinality, mapping checks, key business rules.  
  - *PREP→MART:* dim‑fact coverage, SCD‑2 interval checks, agg/reconciliation, invariants.

- **Scope controls:** layer/datasets (exact, pattern, tags), time window or `batch_id`/files/offsets.

- **Profiles:**  
  - **Smoke** (fast health), **Standard** (default), **Deep** (full + drift/SCD), **Custom** (saved).

- **Gating & tolerances:** severity (blocker/major/minor), gate (fail|warn), abs/pct tolerances; AI can propose tolerances (requires approval).

- **Budget & impact:** time/scan budget; impact‑based selection (changed datasets & downstreams). Plan preview shows test count, ETA, scan volume.

Scheduled/CI runs reuse saved profiles and scopes; new tests from schema changes land as **proposals** (approval required unless policy allows low‑risk auto‑accept).

---

## 9) Minimum Inputs & Acquisition (NEW)

- **Tables & layers:** RAW / PREP (stage/output) / MART, with **grain/keys** and **watermark** columns.  
- **Transform logic:** Prefer **dbt manifest/catalog** or view SQL; otherwise a **Transform Spec (TxSpec)** entered via UI cards (field‑to‑path mappings, filters, explode, rules).  
- **Source alignment:** time window or `batch_id`/file list/offsets; if no source access, **SEP** provides expected metrics.  
- **Policies:** PII redaction on, SQL preview off, external AI off (optional).

---

## 10) API Surface (Backend)

> **All endpoints are versioned (`/api/v1`) and require auth (OIDC).** Responses are JSON; errors follow RFC‑7807.

### 10.1 Catalog
- `POST /catalog/import` → body: Catalog Package JSON **or** dbt artifacts; returns catalog id
- `GET /catalog/:id` → returns catalog JSON; supports ETag/caching
- `GET /catalog/:id/diff/:prev_id` → schema drift diff (adds/removes/type changes)

### 10.2 Datasets & Introspection
- `GET /datasets?catalog_id=...` → list datasets
- `GET /datasets/:name/schema` → columns, PK/FK, watermark
- `GET /datasets/:name/stats` → optional stats (null rate, distinct count, min/max)

### 10.3 Tests & Suites
- `GET /suites` / `POST /suites` / `PUT /suites/:id` / `DELETE /suites/:id`
- `POST /tests/compile` → input: NL/Formula + dataset context → output: `{ir, sql_preview}`
- `POST /tests/propose` → AI proposed cards (batch)
- `POST /suites/:id/run` → triggers a run (returns run_id)

### 10.4 Runs & Reports
- `GET /runs?status=...&suite=...&date_from=...` → list
- `GET /runs/:id` → summary + links
- `GET /runs/:id/results` → paginated test results
- `GET /runs/:id/artifacts` → HTML/JSONL URIs
- `GET /runs/:id/ai/prompts` → prompt log (redacted)

### 10.5 Settings & Security
- `GET/POST /settings/auth-providers`
- `GET/POST /settings/connectors`
- `GET/POST /settings/ai-providers`
- `GET/POST /settings/policies`

### 10.6 Health & Meta
- `GET /healthz`, `GET /readyz`, `GET /version`

---

## 11) Web UI (Pages & UX)

1. **Home / Run History** — filters (suite/env/status), sortable table, deep links  
2. **Test Builder (Zero‑SQL Cards)** — dynamic by schema/stats; AI **Propose** / **Compile**; IR preview; YAML copy  
3. **Datasets & Catalog** — schema viewer, drift diffs, basic lineage graph  
4. **Run Details** — summary, metrics, masked samples, **Failure Explainer**, artifacts download  
5. **Settings** — connections, auth providers, AI providers, policies, roles

UX: keyboard shortcuts, optimistic updates, dark/light, inline diffs.  
Security: OIDC login, role‑gated actions, CSRF, strict CORS (same‑site).

---

## 12) AuthN/AuthZ, Policies, Security

- **RBAC roles:** `admin`, `maintainer`, `viewer`  
- **Policies:** *No external AI*, *No sample rows*, *SQL preview disabled*, *Static secrets forbidden*  
- **Optional Admin Power Mode:** SQL preview **read‑only**, statically analyzed (deny‑list, no DDL/DML), sandboxed, extra approval. Off by default.  
- **DB access:** read‑only; `SELECT` & `EXPLAIN` only; allowlists  
- **Network:** private execution; PrivateLink/peering/VPN; IP allowlist/mTLS  
- **Secrets:** Vault/SM; ephemeral creds preferred; zero on‑disk secrets  
- **PII:** redaction; masked samples with LIMIT; retention configurable

---

## 13) Deployment, CI/CD, Extensibility, AI Features, OSS, Risks, Roadmap

(Sections remain as in v1.1; unchanged content applies.)

- **Deployment & Environments:** Dev (Docker Compose), Prod (K8s + Helm), autoscaling workers.  
- **CI/CD:** Actions/ADO templates, quality gates, SBOM.  
- **Extensibility (SPIs):** Connector/Test‑Type/Auth/AI providers.  
- **AI Features (Phased):** Suggest/Compile/Explain (MVP), Dynamic thresholds & Drift summaries (P2), NLQ & Synthetic (P3).  
- **OSS & License:** Core under Apache‑2.0; dbt Core/GX/Soda/OpenLineage optional (OSS); dbt Cloud optional/paid.  
- **Risks & Mitigations:** over‑wide queries, false positives, secret sprawl, AI drift, air‑gapped freshness.  
- **Roadmap:** P0 infra → P1 Zero‑SQL → P2 connectors/thresh/lineage/RBAC/Helm → P3 NLQ/synthetic/Databricks/Trino.

---

## 14) Glossary

- **Zero‑SQL:** Users never write SQL; AI compiler & cards generate it behind the scenes.  
- **Push‑down:** Execute logic inside the source warehouse/DB, minimizing data movement.  
- **Catalog Package:** JSON snapshot of schema/lineage/stats used by UI & compiler (no rows).  
- **IR/AST:** Intermediate representation; DB‑agnostic logical plan used for SQL generation.  
- **SEP (Source Evidence Package):** Lightweight expected‑metrics bundle for Source→RAW reconciliation when the source isn’t accessible.  
- **TxSpec (Transform Spec):** Declarative mapping/rules description for PREP/MART when dbt or view SQL is unavailable.
