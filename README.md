# Data Testing Orchestrator (DTO)

**Zero-SQL, AI-assisted, push-down data testing framework**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 🚀 Quick Start

Get DTO running in under 5 minutes:

```bash
# Clone the repository
git clone https://github.com/dataflowguard/dto.git
cd dto

# Start the development environment
make dev

# Access the services
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - MinIO Console: http://localhost:9001
```

## 📋 What is DTO?

DTO is a **Zero-SQL, AI-assisted, push-down** data testing framework that enables data engineers to define comprehensive data quality tests without writing SQL. Key features:

- **🧠 AI-Powered**: Natural language test definitions compiled to optimized SQL
- **🔒 Security-First**: SELECT-only queries, PII redaction, policy enforcement
- **⚡ Push-Down Execution**: Tests run inside your data warehouse for performance
- **🎯 Zero-SQL**: Dynamic UI cards for test creation, no SQL knowledge required
- **📊 Comprehensive Reports**: HTML + JSONL artifacts with detailed results
- **🔄 CI/CD Ready**: CLI-first design with deterministic execution

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Data Sources  │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Snowflake,   │
│                 │    │                 │    │    Postgres)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   AI Service    │◄─────────────┘
                        │   (Local LLM)   │
                        └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** (Python 3.11+) - High-performance API framework
- **SQLAlchemy 2.x** - Database ORM with async support
- **Pydantic v2** - Data validation and serialization
- **Typer** - CLI framework
- **PyArrow + DuckDB** - File processing for air-gapped mode

### Frontend
- **Next.js 14** (App Router) - React framework
- **TypeScript 5+** - Type safety
- **TailwindCSS + shadcn/ui** - Modern UI components
- **TanStack Query** - Server state management
- **React Hook Form + Zod** - Form handling and validation

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **Kubernetes + Helm** - Orchestration
- **PostgreSQL 15+** - Run store database
- **S3-compatible storage** - Artifact storage

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/dataflowguard/dto.git
   cd dto
   make setup  # Install dependencies and setup pre-commit hooks
   ```

2. **Start services:**
   ```bash
   make dev  # Starts all services with docker-compose
   ```

3. **Development workflow:**
   ```bash
   make lint      # Run linters
   make test      # Run tests
   make fmt       # Format code
   make openapi   # Generate API documentation
   ```

### Manual Setup (without Make)

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
uvicorn dto_api.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Services:**
```bash
cd infra
docker-compose up postgres minio -d
```

## 📖 Usage Examples

### CLI Usage

```bash
# Check API health
dto health

# Import a catalog
dto import-catalog catalog.json --source-type catalog_package --env dev

# Propose tests for datasets
dto propose RAW.ORDERS PREP.ORDERS --catalog-id abc123 --profile standard

# Compile a natural language test
dto compile "order total should equal items + tax + shipping" --dataset PREP.ORDERS

# Run a test suite
dto run orders_basic --follow

# Check run status
dto status run-id-12345
```

### API Usage

```python
import httpx

# Create API client
client = httpx.Client(base_url="http://localhost:8000/api/v1")

# Import catalog
response = client.post("/catalog/import", json={
    "source_type": "catalog_package",
    "data": catalog_data,
    "environment": "dev"
})

# Propose tests
response = client.post("/tests/propose", json={
    "datasets": ["RAW.ORDERS", "PREP.ORDERS"],
    "catalog_id": "abc123",
    "profile": "standard"
})

# Run test suite
response = client.post("/suites/orders_basic/run", json={
    "dry_run": False,
    "budget_seconds": 900
})
```

### Web UI

1. **Test Builder**: Create tests using dynamic cards
2. **Run History**: View execution results and trends
3. **Datasets**: Browse catalog and schema information
4. **Settings**: Configure connections, policies, and AI providers

## 🔒 Security Features

DTO implements security-first design principles:

- **SELECT-only enforcement**: All database queries are validated to prevent DDL/DML
- **PII redaction**: Automatic detection and masking of sensitive data
- **Policy controls**: Configurable security policies with secure defaults
- **Network isolation**: Support for VPC/private network deployment
- **Audit logging**: Comprehensive logging of all operations
- **Secret management**: Integration with Vault, AWS Secrets Manager, etc.

### Default Security Policies

```yaml
# Secure defaults (as specified in BRD)
external_ai_enabled: false        # No external AI by default
sql_preview_enabled: false        # SQL preview disabled
admin_power_mode: false          # Admin SQL preview disabled
pii_redaction_enabled: true      # PII redaction enabled
static_secrets_forbidden: true   # Static secrets blocked
network_isolation: true          # Network isolation required
```

## 📊 Test Types Supported

### Core Test Families
- **Schema/Contract**: Column presence, types, constraints
- **Integrity**: Primary key uniqueness, foreign key validity, not-null checks
- **Reconciliation**: Row counts, aggregate comparisons, cross-system validation
- **Freshness**: Data recency, SLA compliance, late arrival detection
- **Business Rules**: Custom logic validation with tolerance handling
- **Drift Detection**: Schema changes, data distribution shifts

### JSON/VARIANT Support
- **JSON validity**: Parse error detection and reporting
- **Path existence**: Required field validation
- **Type checking**: Data type enforcement for JSON fields
- **Schema versioning**: Version compatibility validation
- **Flatten cardinality**: Array expansion validation
- **Mapping equivalence**: Source-to-target field mapping validation

## 🚀 Deployment

### Docker Compose (Development)
```bash
cd infra
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Using Helm
helm install dto ./infra/helm/dto \
  --set api.image.tag=0.1.0 \
  --set frontend.image.tag=0.1.0 \
  --set postgresql.auth.password=secure-password

# Using kubectl
kubectl apply -f infra/k8s/
```

### Terraform (Infrastructure)
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## 🔧 Configuration

### Environment Variables

**API Backend:**
```bash
DATABASE_URL=postgresql://dto:dto@localhost:5432/dto
ARTIFACT_STORAGE_TYPE=s3
ARTIFACT_STORAGE_CONFIG={"bucket": "dto-artifacts", "region": "us-east-1"}
EXTERNAL_AI_ENABLED=false
SQL_PREVIEW_ENABLED=false
PII_REDACTION_ENABLED=true
LOG_LEVEL=INFO
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Database Connections

```yaml
# Example connection configuration
connections:
  - name: snowflake_prod
    type: snowflake
    host: account.snowflakecomputing.com
    database: PROD_DWH
    warehouse: COMPUTE_WH
    role: DTO_READER
    auth_method: iam
    read_only: true
```

## 📈 Monitoring & Observability

DTO provides comprehensive observability:

- **Metrics**: Prometheus metrics for API, tests, and AI operations
- **Logging**: Structured JSON logs with request tracing
- **Health Checks**: Kubernetes-ready health and readiness probes
- **Dashboards**: Grafana dashboards for monitoring test execution

### Key Metrics
- `dto_test_executions_total` - Total test executions by type and status
- `dto_api_requests_total` - API request metrics
- `dto_ai_requests_total` - AI service interaction metrics
- `dto_active_runs` - Currently running test suites

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run `make lint test`
6. Submit a pull request

### Code Standards
- **Backend**: Black formatting, Ruff linting, MyPy type checking
- **Frontend**: ESLint + Prettier, TypeScript strict mode
- **Tests**: Pytest with >80% coverage requirement
- **Documentation**: Clear docstrings and README updates

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/dataflowguard/dto/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dataflowguard/dto/discussions)
- **Email**: team@dataflowguard.com

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core API and CLI framework
- ✅ Basic test types and AI compilation
- ✅ Security policies and guardrails
- ✅ Docker and Kubernetes deployment

### Phase 2 (Next)
- 🔄 Real database connectors (Snowflake, BigQuery, Postgres)
- 🔄 Advanced AI features and local LLM integration
- 🔄 Enhanced UI with test builder cards
- 🔄 Comprehensive monitoring and alerting

### Phase 3 (Future)
- 📋 Advanced lineage and impact analysis
- 📋 Synthetic data generation
- 📋 Natural language query interface
- 📋 Advanced drift detection and ML-based anomaly detection

## 🔄 CI/CD & Quality Gates

DTO uses GitHub Actions for continuous integration and security scanning:

### Required Checks
All pull requests must pass these automated checks:

- **Python CI**: Linting (ruff), type checking (mypy), unit tests (pytest)
- **Frontend CI**: ESLint, TypeScript compilation, Jest tests, Next.js build
- **Security Audit**: Dependency vulnerability scanning (pip-audit, npm audit)
- **SBOM Generation**: Software Bill of Materials for compliance
- **Container Scanning**: Trivy security scans for Docker images
- **Secrets Detection**: TruffleHog scan for exposed credentials

### Branch Protection
Configure these branch protection rules for `main`:

```yaml
Required status checks:
  - Python CI
  - Frontend CI
  - Dependency Security Audit
  - Generate SBOM
  
Require branches to be up to date: ✓
Require pull request reviews: ✓ (1 reviewer minimum)
Dismiss stale reviews: ✓
Restrict pushes to matching branches: ✓
```

### Artifacts
CI generates these artifacts for compliance and debugging:
- **Coverage Reports**: Python test coverage (XML format)
- **SBOM**: Software Bill of Materials (SPDX + CycloneDX formats)
- **Security Reports**: Vulnerability scans and audit results
- **Build Artifacts**: Frontend builds and test results

### Running Checks Locally
```bash
# Python checks
cd backend
ruff check dto_api/ dto_cli/ tests/
mypy dto_api/ dto_cli/
pytest tests/ -v -m "not integration"

# Frontend checks  
cd frontend
npm run lint
npx tsc --noEmit
npm test
npm run build

# Security checks
pip-audit --desc
npm audit --audit-level=high
```

---

**Built with ❤️ by the DataFlowGuard team**