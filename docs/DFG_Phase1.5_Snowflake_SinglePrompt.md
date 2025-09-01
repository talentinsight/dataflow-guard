# DataFlowGuard — Cursor Development Prompt (Phase 1.5, Snowflake Real, Single Prompt)

**Apply this AFTER Phase 0–1 scaffold is generated.**  
**Scope:** Make Snowflake **real** (read‑only connector + runner + EXPLAIN pre‑check + SELECT‑only guardrails + minimal SEP validation) in strict compliance with **BRD/TDR v1.2**.

---

## SYSTEM MANDATE (Non‑Negotiable)

Implement the deliverables below **exactly**. Treat all “Hard Rules” as tests. Output must be runnable via `docker compose up` and pass the Acceptance Checklist.

### Hard Rules (Security & Determinism)
1) **SELECT‑only**: Single statement; **reject** any DDL/DML/transaction. Deny keywords (case‑insensitive):  
   `INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|CALL|USE|COPY|PUT|GET|BEGIN|COMMIT|ROLLBACK`
2) **EXPLAIN pre‑check**: For every SELECT, run `EXPLAIN USING TEXT` first. If plan fails or **budget** exceeded, **block** execution.
3) **Determinism**: `temperature=0`, `top_p=1` (if any AI path is used), fixed **seed**, explicit **timeouts**.
4) **Secrets**: Read from **env** (or Vault stub), **never log** creds. Mask sensitive fields on all API responses.
5) **PII redaction**: Enabled by default for any returned rows/samples. (Mask: hash/email mask/last4, configurable.)
6) **Network**: No outbound egress except Snowflake endpoint (configurable domain allowlist). Respect proxy settings.
7) **Auditability**: Log `query_id`, timing, bytes scanned, and store immutable artifacts (HTML/JSONL). No raw PII in logs.

---

## ENVIRONMENT VARIABLES (Embed in code & docs)

### Snowflake connection (required for real runs)
```
SNOWFLAKE_ACCOUNT=xy12345.eu-west-1
SNOWFLAKE_USER=dfg_runner
# choose ONE auth method:
SNOWFLAKE_PASSWORD=****************
# or key pair:
SNOWFLAKE_PRIVATE_KEY_PATH=/run/secrets/snowflake_rsa_key
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=********

SNOWFLAKE_ROLE=DFG_RO
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_DATABASE=PROD_DB
SNOWFLAKE_SCHEMA=RAW   # default schema, can be overridden per request
SNOWFLAKE_REGION=eu-west-1   # optional
SNOWFLAKE_HOST=xy12345.snowflakecomputing.com  # optional explicit host
```

### Runner budgets & safety
```
DFG_SELECT_TIMEOUT=60                # seconds hard statement timeout
DFG_SCAN_BUDGET_BYTES=0              # 0=disabled; else block when bytes scanned exceeds this
DFG_SAMPLE_LIMIT=1000                # cap for preview/sample selects
DFG_ALLOWED_SCHEMAS=PROD_DB.RAW,PROD_DB.PREP,PROD_DB.MART
DFG_NETWORK_ALLOWLIST=*.snowflakecomputing.com
DFG_QUERY_TAG=DataFlowGuard
DFG_LOG_PII=false                    # never log PII
```

### Optional proxy / Vault stub
```
HTTP_PROXY=
HTTPS_PROXY=
NO_PROXY=localhost,127.0.0.1
VAULT_ADDR=
VAULT_TOKEN=
```

Create `backend/.env.example` with the variables above; compose should load `.env` automatically.

---

## DELIVERABLES

### 1) Snowflake connector (REAL, read‑only)
Create `backend/dto_api/adapters/connectors/snowflake.py` exposing:

```python
class SnowflakeConnector:
    def __init__(self, settings): ...
    def test_connection(self) -> dict: ...
    def explain(self, sql: str) -> dict: ...      # plan text + parsed hints if any
    def select(self, sql: str, limit: int | None = None) -> dict: ...
```

Implementation details:
- Use `snowflake-connector-python`. On connect: set `QUERY_TAG=DFG_QUERY_TAG`, `STATEMENT_TIMEOUT_IN_SECONDS=DFG_SELECT_TIMEOUT`.
- Attach `ROLE`, `WAREHOUSE`, `DATABASE`, `SCHEMA` when provided.
- **Guard**: Validate SQL with denylist & single‑statement check **before** EXPLAIN/SELECT.
- **EXPLAIN**: Run `EXPLAIN USING TEXT <SELECT...>`; include plan text in result.
- **SELECT**: Execute only after EXPLAIN passes. Apply `LIMIT` if provided via `DFG_SAMPLE_LIMIT` for previews.
- After SELECT, fetch metrics from `INFORMATION_SCHEMA.QUERY_HISTORY` via `sfqid` (bytes scanned, elapsed, rows produced).
- Return structure:
```json
{ "query_id":"...", "rows":[{"col":"masked_val", "...": "..."}],
  "stats":{"bytes_scanned":12345,"elapsed_ms":678,"rows":10},
  "plan_text":"...", "warehouse":"...", "role":"..." }
```

### 2) Settings API & masking
- Extend `POST/GET /api/v1/settings/connectors` to persist Snowflake settings. On GET, mask secrets (`******`).
- Add `POST /api/v1/settings/connectors/test-connection` calling `SnowflakeConnector.test_connection()`.

### 3) Runner (minimal, real, SELECT‑only)
- Implement `backend/dto_api/services/runner.py` with flow:
  1) Receive test/suite → compile (if needed) → produce SQL string(s). Enforce **one statement per request**.
  2) **Validate** (denylist + allowed schemas via `DFG_ALLOWED_SCHEMAS`).
  3) **EXPLAIN** → parse, check **DFG_SCAN_BUDGET_BYTES** if present (estimate/heuristic or post‑facto block + warn).
  4) Execute **SELECT**, **mask** samples (PII redaction stub), write **HTML + JSONL** artifacts.
  5) Persist `query_id`, timing, rows, bytes, plan hash, and policy flags used.

### 4) RAW JSON (VARIANT) compile path
- In `POST /api/v1/tests/compile`, support JSON path/flatten cards and emit Snowflake SQL using `LATERAL FLATTEN(input => t.payload)`.
- Deterministic output. Include at least 1 unit test converting IR → SQL with FLATTEN.

### 5) SEP (Source Evidence Package) minimal validation
- Add `POST /api/v1/sep/validate` accepting:
```json
{ "raw_table": "PROD_DB.RAW.ORDERS",
  "window": {"column":"EVENT_TS","from":"2025-01-01T00:00:00Z","to":"2025-01-02T00:00:00Z"},
  "manifest": {"batch_id":"2025-01-01","expected_rowcount":100000,
               "control_totals":{"SUM_amount":1234567.89,"DISTINCT_order_id":99999,
                                 "MIN_ts":"2025-01-01T00:00:00Z","MAX_ts":"2025-01-01T23:59:59Z"}},
  "tolerances": {"rowcount_abs":0, "totals_pct":0.5}
}
```
- Compute the same metrics over Snowflake within the window and return a reconciliation report.

### 6) Frontend updates
- **Settings → Connectors**: form for Snowflake fields, save via API, **Test Connection** button.
- **Builder**: when dataset kind = RAW/JSON, add a **Flatten Preview** panel calling `/tests/compile` and showing read‑only SQL preview.
- **Run Details**: display `query_id`, bytes scanned, elapsed; link to artifacts.

### 7) Docker/Deps/CI
- Add `snowflake-connector-python` to backend deps. Ensure cryptography/openssl wheels work in container.
- Compose: pass through `.env`. Disable external egress except Snowflake (document how to enforce via network policies).
- CI: Mark Snowflake tests as `@integration` and skip unless Snowflake env vars are set.

### 8) Tests
- **Unit:** SQL validator (reject DDL/DML/multi‑stmt/forbidden keywords); Allowed schema check.
- **Unit:** Settings masking.
- **Unit:** IR → SQL with `LATERAL FLATTEN` for JSON arrays.
- **Integration (optional):** `test_snowflake_connection` and a sample `SELECT 1` run producing artifacts (skipped if no env).

---

## SECURITY POLICIES (Embed docs & defaults)

1) **RBAC on Snowflake:** Use a read‑only role (e.g., `DFG_RO`) with `USAGE` on Warehouse/DB/Schema and `SELECT` on target schemas only. Include “future tables” grants.
2) **Query Tagging:** Set `QUERY_TAG=DataFlowGuard` on session for audit.
3) **Statement Timeout:** Enforce via session param and server‑side timeout; default `DFG_SELECT_TIMEOUT=60`.
4) **Scan Budget:** Block when `bytes_scanned > DFG_SCAN_BUDGET_BYTES` (if >0).
5) **PII Redaction:** Always apply masking to returned samples; configurable strategies (hash/email mask/last4).
6) **No Secrets in Logs:** Redact envs; never echo passwords/keys.
7) **Network Control:** Egress allowlist to Snowflake only; support corporate proxy; document PrivateLink/IP allowlist if applicable.
8) **SQL Preview Policy:** Keep **read‑only**; show only `SELECT` previews; never execute previews without EXPLAIN.
9) **Artifacts Retention:** Store HTML/JSONL with masked samples; retention configurable; hash plan text for audit.

SQL example for Snowflake role (doc only):
```sql
CREATE ROLE DFG_RO;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DFG_RO;
GRANT USAGE ON DATABASE PROD_DB TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.RAW  TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.PREP TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.MART TO ROLE DFG_RO;
GRANT SELECT ON ALL TABLES    IN SCHEMA PROD_DB.RAW  TO ROLE DFG_RO;
GRANT SELECT ON ALL VIEWS     IN SCHEMA PROD_DB.RAW  TO ROLE DFG_RO;
GRANT SELECT ON ALL TABLES    IN SCHEMA PROD_DB.PREP TO ROLE DFG_RO;
GRANT SELECT ON ALL VIEWS     IN SCHEMA PROD_DB.PREP TO ROLE DFG_RO;
GRANT SELECT ON ALL TABLES    IN SCHEMA PROD_DB.MART TO ROLE DFG_RO;
GRANT SELECT ON ALL VIEWS     IN SCHEMA PROD_DB.MART TO ROLE DFG_RO;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DB.RAW  TO ROLE DFG_RO;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DB.PREP TO ROLE DFG_RO;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DB.MART TO ROLE DFG_RO;
```

---

## ACCEPTANCE CHECKLIST

- `docker compose up` → API `:8000`, UI `:3000` healthy.
- `POST /api/v1/settings/connectors` saves Snowflake config (secrets **masked** on GET). `.../test-connection` returns OK.
- `POST /api/v1/tests/compile` returns Snowflake SQL preview with **`LATERAL FLATTEN`** for JSON arrays.
- `POST /api/v1/suites/{id}/run` (with valid env):
  - validates SQL (denylist + allowed schemas),
  - runs **EXPLAIN**, enforces **timeouts/budget**,
  - executes **SELECT** on Snowflake,
  - writes **HTML + JSONL artifacts**, persists `query_id`, bytes, elapsed.
- `POST /api/v1/sep/validate` returns reconciliation report based on given `window` & `manifest`.
- SQL validator **blocks** DDL/DML/multi‑stmt and forbidden keywords.
- No secrets/PII in logs; samples are masked.
- External AI **disabled by default**; all features work without it.

---

## HOW TO APPLY (Cursor)

1) Open the monorepo generated in Phase 0–1.  
2) Paste this **entire** prompt into Cursor.  
3) Ensure the model edits existing files (don’t create a new repo) and runs tests.  
4) Create `backend/.env` from `.env.example`, fill Snowflake creds, then:
   ```bash
   docker compose up --build
   ```
5) Run a sample compile and run via API or CLI. Confirm Acceptance items are green.
