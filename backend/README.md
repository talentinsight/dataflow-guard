# DTO Backend

FastAPI-based backend for the Data Testing Orchestrator.

## Architecture

```
dto_api/
├── main.py              # FastAPI application entry point
├── routers/             # API route handlers
│   ├── catalog.py       # Catalog import/management
│   ├── datasets.py      # Dataset introspection
│   ├── health.py        # Health checks
│   ├── runs.py          # Test execution
│   ├── settings.py      # Configuration
│   └── tests.py         # Test compilation/proposals
├── models/              # Pydantic data models
│   ├── catalog.py       # Catalog package models
│   ├── reports.py       # Run and report models
│   ├── settings.py      # Configuration models
│   └── tests.py         # Test definition models
├── services/            # Business logic
│   ├── ai_adapter_iface.py    # AI service interface
│   ├── catalog_import.py      # Catalog processing
│   ├── planner.py            # Test planning
│   └── runner_stub.py        # Test execution
├── adapters/            # External integrations
│   ├── connectors/      # Database connectors
│   ├── auth/           # Authentication providers
│   └── storage/        # Artifact storage
├── policies/           # Security policies
│   ├── pii_redaction.py     # PII handling
│   └── sql_preview_off.py   # SQL preview control
├── schemas/            # JSON Schema validation
├── telemetry/          # Logging and metrics
└── __init__.py

dto_cli/
├── main.py             # Typer CLI application
└── __init__.py
```

## Development

### Setup
```bash
cd backend
pip install -e ".[dev]"
```

### Running
```bash
# Development server
uvicorn dto_api.main:app --reload

# CLI
python -m dto_cli --help
```

### Testing
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Linting
ruff check dto_api/ dto_cli/ tests/
mypy dto_api/ dto_cli/

# Formatting
black dto_api/ dto_cli/ tests/
ruff --fix dto_api/ dto_cli/ tests/
```

## API Documentation

When running the server, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `ARTIFACT_STORAGE_TYPE`: Storage type (s3, local)
- `ARTIFACT_STORAGE_CONFIG`: Storage configuration JSON
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed CORS origins

## Security

The backend enforces several security policies:
- SELECT-only SQL validation
- PII redaction in samples and AI context
- SQL preview disabled by default
- Static secrets discouraged
- Comprehensive audit logging
