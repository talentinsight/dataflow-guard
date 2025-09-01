# Phase 1.5: Snowflake Real Implementation

This document describes the Phase 1.5 implementation that makes Snowflake **real** with SELECT-only guardrails, EXPLAIN pre-checks, and comprehensive security controls.

## 🎯 Implementation Overview

Phase 1.5 transforms the DTO scaffold into a production-ready system with:

- **Real Snowflake Connector**: Full integration with `snowflake-connector-python`
- **SELECT-only Security**: Comprehensive SQL validation and keyword blocking
- **EXPLAIN Pre-checks**: Query plan analysis before execution
- **JSON/VARIANT Support**: LATERAL FLATTEN compilation for semi-structured data
- **SEP Validation**: Source Evidence Package reconciliation
- **PII Redaction**: Automatic masking of sensitive data
- **Budget Controls**: Query timeout and scan volume limits

## 🔐 Security Implementation

### SQL Validation & Guardrails

The system enforces strict SELECT-only access through multiple layers:

```python
# Forbidden keywords (case-insensitive)
FORBIDDEN = [
    'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'CREATE', 'ALTER', 'DROP',
    'TRUNCATE', 'GRANT', 'REVOKE', 'CALL', 'USE', 'COPY', 'PUT', 'GET',
    'BEGIN', 'COMMIT', 'ROLLBACK', 'SET', 'UNSET'
]
```

**Validation Flow:**
1. **Single Statement Check**: Only one SQL statement per request
2. **Keyword Filtering**: Deny-list validation with regex matching
3. **Schema Access Control**: Optional allowlist of permitted schemas
4. **Comment Stripping**: Remove SQL comments before validation

### EXPLAIN Pre-check Process

Every SELECT query goes through mandatory EXPLAIN analysis:

```python
async def explain(self, sql: str) -> Dict[str, Any]:
    # 1. Validate SQL first
    self._validate_sql(sql)
    
    # 2. Run EXPLAIN USING TEXT
    explain_sql = f"EXPLAIN USING TEXT {sql}"
    cursor.execute(explain_sql)
    
    # 3. Check scan budget if configured
    estimated_bytes = self._estimate_scan_bytes(plan_text)
    if self.scan_budget_bytes > 0 and estimated_bytes > self.scan_budget_bytes:
        raise ValueError(f"Estimated scan exceeds budget")
    
    return result
```

### PII Redaction

Automatic PII detection and masking:

- **Email addresses**: `john.doe@example.com` → `j***@***.com`
- **SSN patterns**: `123-45-6789` → `***-**-6789`
- **Credit cards**: `4111-1111-1111-1111` → `****-****-****-1111`
- **Phone numbers**: `(555) 123-4567` → `(***) ***-4567`

## 🏗️ Architecture Components

### Snowflake Connector (`snowflake.py`)

**Core Features:**
- Environment-based configuration
- Password or private key authentication
- Connection pooling and reuse
- Query metrics collection
- Automatic PII redaction

**Security Controls:**
- SQL validation before execution
- EXPLAIN mandatory pre-check
- Configurable scan budgets
- Schema access restrictions
- Query tagging for audit

### Real Runner Service (`runner.py`)

**Execution Flow:**
1. **Compile Tests**: Convert test definitions to SQL
2. **Validate SQL**: Apply security guardrails
3. **EXPLAIN Check**: Analyze execution plan
4. **Execute SELECT**: Run validated query
5. **Generate Artifacts**: Create HTML/JSONL reports

**Artifact Generation:**
- **HTML Reports**: Rich, interactive test results
- **JSONL Logs**: Machine-readable audit trail
- **Sample Data**: Masked violation examples
- **Query Metrics**: Performance and scan statistics

### JSON/VARIANT Compilation

Support for semi-structured data testing with Snowflake-specific SQL:

```sql
-- JSON Path Existence
SELECT 
    COUNT(*) as total_rows,
    COUNT(GET_PATH(payload, '$.id')) as path_exists_count
FROM RAW.EVENTS;

-- Array Flatten Cardinality
WITH flattened AS (
    SELECT f.value as item
    FROM RAW.ORDERS t,
    LATERAL FLATTEN(input => GET_PATH(t.payload, '$.items')) f
)
SELECT COUNT(*) as flattened_count FROM flattened;

-- Type Validation
SELECT 
    COUNT(CASE WHEN TYPEOF(GET_PATH(payload, '$.amount')) = 'NUMBER' THEN 1 END) as correct_type
FROM RAW.EVENTS;
```

### SEP Validation Endpoint

Source Evidence Package validation for air-gapped reconciliation:

```python
POST /api/v1/sep/validate
{
  "raw_table": "PROD_DB.RAW.ORDERS",
  "window": {
    "column": "EVENT_TS",
    "from": "2025-01-01T00:00:00Z",
    "to": "2025-01-02T00:00:00Z"
  },
  "manifest": {
    "batch_id": "2025-01-01",
    "expected_rowcount": 100000,
    "control_totals": {
      "SUM(amount)": 1234567.89,
      "DISTINCT(order_id)": 99999
    }
  },
  "tolerances": {
    "rowcount_abs": 0,
    "totals_pct": 0.5
  }
}
```

## 🔧 Configuration

### Environment Variables

**Snowflake Connection:**
```bash
SNOWFLAKE_ACCOUNT=xy12345.eu-west-1
SNOWFLAKE_USER=dfg_runner
SNOWFLAKE_PASSWORD=****************  # OR private key
SNOWFLAKE_ROLE=DFG_RO
SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
SNOWFLAKE_DATABASE=PROD_DB
SNOWFLAKE_SCHEMA=RAW
```

**Security & Budget Controls:**
```bash
DFG_SELECT_TIMEOUT=60                # Query timeout (seconds)
DFG_SCAN_BUDGET_BYTES=0              # Scan budget (0=disabled)
DFG_SAMPLE_LIMIT=1000                # Sample row limit
DFG_ALLOWED_SCHEMAS=PROD_DB.RAW,PROD_DB.PREP,PROD_DB.MART
DFG_QUERY_TAG=DataFlowGuard          # Snowflake query tag
DFG_LOG_PII=false                    # Never log PII
```

**Policy Defaults:**
```bash
EXTERNAL_AI_ENABLED=false            # AI disabled by default
SQL_PREVIEW_ENABLED=false            # No SQL preview
PII_REDACTION_ENABLED=true           # PII redaction on
STATIC_SECRETS_FORBIDDEN=true        # Discourage static secrets
```

### Snowflake RBAC Setup

Recommended role configuration:

```sql
-- Create read-only role
CREATE ROLE DFG_RO;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DFG_RO;

-- Grant database/schema access
GRANT USAGE ON DATABASE PROD_DB TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.RAW TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.PREP TO ROLE DFG_RO;
GRANT USAGE ON SCHEMA PROD_DB.MART TO ROLE DFG_RO;

-- Grant SELECT permissions
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DB.RAW TO ROLE DFG_RO;
GRANT SELECT ON ALL VIEWS IN SCHEMA PROD_DB.RAW TO ROLE DFG_RO;
GRANT SELECT ON FUTURE TABLES IN SCHEMA PROD_DB.RAW TO ROLE DFG_RO;
-- Repeat for PREP and MART schemas

-- Create service user
CREATE USER dfg_runner 
  PASSWORD = '***' 
  DEFAULT_ROLE = DFG_RO
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE DFG_RO TO USER dfg_runner;
```

## 🧪 Testing Strategy

### Unit Tests

**SQL Validation Tests** (`test_snowflake_security.py`):
- SELECT statements allowed
- DDL/DML statements blocked
- Multi-statement queries rejected
- Case-insensitive keyword detection
- Schema access control validation

**JSON Compilation Tests** (`test_json_compilation.py`):
- LATERAL FLATTEN SQL generation
- JSON path existence checks
- Array cardinality validation
- Type checking compilation
- Mapping equivalence tests

### Integration Tests

**Snowflake Integration** (`test_snowflake_integration.py`):
- Real connection testing
- Query execution with metrics
- EXPLAIN functionality
- PII redaction verification
- Budget enforcement (if configured)

**Test Execution:**
```bash
# Unit tests only
pytest tests/ -m "not integration"

# Integration tests (requires Snowflake credentials)
pytest tests/ -m "integration"

# All tests
pytest tests/
```

### CI/CD Integration

GitHub Actions automatically:
- Runs unit tests on every PR
- Runs integration tests if Snowflake secrets are configured
- Skips integration tests gracefully if credentials unavailable
- Generates coverage reports
- Validates OpenAPI specification

## 🚀 Deployment

### Docker Compose

Updated `docker-compose.yml` includes:
- Snowflake environment variable pass-through
- Security policy defaults
- Network restrictions (Snowflake endpoints only)

```bash
# Copy environment template
cp backend/env.example backend/.env

# Configure Snowflake credentials
vim backend/.env

# Start services
docker compose up --build
```

### Kubernetes Deployment

Helm chart includes:
- Snowflake credential management via secrets
- Security policy configuration
- Network policies for egress control
- Resource limits and budgets

### Production Checklist

**Security:**
- [ ] Snowflake role has minimal required permissions
- [ ] Static secrets replaced with dynamic credentials
- [ ] Network egress restricted to Snowflake endpoints
- [ ] PII redaction policies configured
- [ ] Query budgets and timeouts set

**Monitoring:**
- [ ] Query metrics exported to Prometheus
- [ ] Audit logs configured for security events
- [ ] Alert rules for budget violations
- [ ] Dashboard for query performance

**Compliance:**
- [ ] Data retention policies configured
- [ ] Audit trail immutability verified
- [ ] PII handling documented
- [ ] Access controls reviewed

## 📊 Performance & Monitoring

### Query Metrics

Every query execution captures:
- **Query ID**: Snowflake query identifier
- **Execution Time**: End-to-end timing
- **Bytes Scanned**: Data volume processed
- **Rows Returned**: Result set size
- **Plan Hash**: Execution plan fingerprint

### Prometheus Metrics

Exported metrics include:
- `dto_queries_total`: Query count by status
- `dto_query_duration_seconds`: Query execution time
- `dto_bytes_scanned_total`: Cumulative bytes scanned
- `dto_budget_violations_total`: Budget violation count

### Audit Logging

Structured JSON logs capture:
- All SQL queries (with PII redaction)
- Security policy violations
- Budget enforcement actions
- Authentication events
- Configuration changes

## 🔍 Troubleshooting

### Common Issues

**Connection Failures:**
```bash
# Test connection manually
curl -X POST http://localhost:8000/api/v1/settings/connections/test-connection \
  -H "Content-Type: application/json" \
  -d '{"type":"snowflake","account":"...","user":"..."}'
```

**SQL Validation Errors:**
- Check for forbidden keywords in queries
- Verify single statement requirement
- Review schema access permissions

**Budget Violations:**
- Adjust `DFG_SCAN_BUDGET_BYTES` if too restrictive
- Optimize queries to reduce scan volume
- Use sampling for large datasets

**PII Redaction Issues:**
- Review redaction patterns in `pii_redaction.py`
- Configure custom PII detection rules
- Verify masking is applied to all outputs

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG
DFG_LOG_PII=true  # Only in development!
```

## 📈 Next Steps (Phase 2)

Phase 1.5 provides the foundation for:
- **Additional Connectors**: PostgreSQL, BigQuery, Redshift
- **Advanced AI Integration**: Local LLM deployment
- **Enhanced Catalog Management**: Schema drift detection
- **Workflow Orchestration**: Airflow/dbt integration
- **Advanced Security**: Vault integration, mTLS

The system is now production-ready for Snowflake environments with comprehensive security controls and real data testing capabilities.
