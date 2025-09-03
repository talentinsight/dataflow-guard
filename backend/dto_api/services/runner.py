import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

import structlog
from sqlalchemy.orm import Session

from dto_api.models.reports import (
    RunRequest,
    RunResponse,
    RunSummary,
    RunListRequest,
    RunListResponse,
    ReportRecord
)
from dto_api.models.tests import TestResult, TestDefinition, TestSuite
from dto_api.adapters.connectors.snowflake import SnowflakeConnector
from dto_api.services.ai_adapter_iface import AIAdapterInterface
from dto_api.services.compile_service import compile_service
from dto_api.services.artifact_service import artifact_service
from dto_api.policies.pii_redaction import PIIRedactionPolicy
from dto_api.db.models import Run, RunTest, Artifact, get_db_manager

logger = structlog.get_logger()

class RunnerService:
    """Real test runner service for executing test suites with Snowflake."""

    def __init__(self):
        self.ai_adapter = AIAdapterInterface()
        self.pii_policy = PIIRedactionPolicy(enabled=True)
        self.snowflake_connector: Optional[SnowflakeConnector] = None

    async def execute_suite(self, request: RunRequest) -> RunResponse:
        """Execute a test suite with real Snowflake connector."""
        db_manager = get_db_manager()
        try:
            # Get test suite (mock for now)
            suite = await self._get_test_suite(request.suite_id)
            if not suite:
                raise ValueError(f"Test suite '{request.suite_id}' not found")

            # Create run record in database
            with db_manager.get_session() as session:
                run_record = Run(
                    id=str(uuid.uuid4()),
                    suite_name=suite.name,
                    status="running",
                    started_at=datetime.utcnow(),
                    environment="dev",
                    connection=request.connection_override or suite.connection
                )
                session.add(run_record)
                session.commit()
                run_id = str(run_record.id)

            if not request.dry_run:
                # Start background execution
                asyncio.create_task(self._execute_tests_real(run_id, suite, request))
                status = "running"
            else:
                # For dry run, validate and return
                await self._validate_tests(suite)
                # Update run record for dry run
                with db_manager.get_session() as session:
                    run_record = session.query(Run).filter(Run.id == run_id).first()
                    if run_record:
                        run_record.status = "completed"
                        run_record.finished_at = datetime.utcnow()
                        run_record.duration_ms = 100
                        session.commit()
                status = "completed"

            estimated_duration = 300 if not request.dry_run else 5

            return RunResponse(
                run_id=run_id,
                status=status,
                estimated_duration_seconds=estimated_duration
            )

        except Exception as e:
            logger.error("Failed to start test execution", exc_info=e)
            raise

    async def _get_test_suite(self, suite_id: str) -> Optional[TestSuite]:
        """Get test suite by ID (mock implementation)."""
        # Mock test suite for demo
        return TestSuite(
            id=suite_id,
            name="Demo Test Suite",
            description="E2E demo test suite for Snowflake",
            connection="snowflake",
            tests=[
                TestDefinition(
                    id="row-count-test",
                    name="Row Count Test",
                    type="row_count",
                    dataset="DEMO_DB.PUBLIC.SAMPLE_TABLE",
                    description="Check row count"
                ),
                TestDefinition(
                    id="schema-test", 
                    name="Schema Validation",
                    type="schema",
                    dataset="DEMO_DB.PUBLIC.SAMPLE_TABLE",
                    description="Validate table schema"
                )
            ]
        )

    async def _validate_tests(self, suite: TestSuite) -> None:
        """Validate test suite configuration."""
        for test in suite.tests:
            if not test.dataset:
                raise ValueError(f"Test '{test.name}' missing dataset")
            if test.type not in ["row_count", "schema", "null_check", "duplicate_check"]:
                raise ValueError(f"Unsupported test type: {test.type}")

    async def _execute_tests_real(self, run_id: str, suite: TestSuite, request: RunRequest) -> None:
        """Execute tests with real Snowflake connector."""
        db_manager = get_db_manager()
        start_time = datetime.utcnow()

        try:
            logger.info("Starting real test execution", run_id=run_id, suite_name=suite.name)

            # Initialize Snowflake connector
            if not self.snowflake_connector:
                self.snowflake_connector = SnowflakeConnector()
                await self.snowflake_connector.connect()

            # Convert test definitions to compilation format
            test_templates = []
            for test in suite.tests:
                if request.test_filter and test.name not in request.test_filter:
                    continue

                test_template = {
                    "name": test.name,
                    "type": test.type,
                    "dataset": test.dataset
                }

                # Add test-specific parameters
                if test.type == "row_count":
                    test_template.update({
                        "expected_min": getattr(test, "expected_min", 0),
                        "expected_max": getattr(test, "expected_max", None)
                    })
                elif test.type == "schema":
                    test_template["expected_columns"] = getattr(test, "expected_columns", [])
                elif test.type == "null_check":
                    test_template.update({
                        "column": getattr(test, "column", "id"),
                        "expected_nulls": getattr(test, "expected_nulls", 0)
                    })
                elif test.type == "duplicate_check":
                    test_template.update({
                        "keys": getattr(test, "keys", ["id"]),
                        "expected_duplicates": getattr(test, "expected_duplicates", 0)
                    })

                test_templates.append(test_template)

            if not test_templates:
                logger.warning("No tests to execute after filtering", run_id=run_id)
                return

            # Compile tests to SQL
            compilation_result = compile_service.compile_tests(test_templates)
            compiled_tests = compilation_result["tests"]

            # Execute each test
            query_ids = []
            with db_manager.get_session() as session:
                for i, compiled_test in enumerate(compiled_tests):
                    test_start = datetime.utcnow()

                    try:
                        # Execute SQL against Snowflake
                        result_rows = await self.snowflake_connector.execute_query(
                            compiled_test["sql"]
                        )

                        test_end = datetime.utcnow()
                        duration_ms = int((test_end - test_start).total_seconds() * 1000)

                        # Extract query ID if available
                        query_id = getattr(self.snowflake_connector, 'last_query_id', None)
                        if query_id:
                            query_ids.append(query_id)

                        # Evaluate test result
                        status, observed = self._evaluate_test_result(
                            compiled_test, result_rows
                        )

                        # Create test record
                        test_record = RunTest(
                            run_id=run_id,
                            name=compiled_test["name"],
                            type=compiled_test["type"],
                            status=status,
                            started_at=test_start,
                            finished_at=test_end,
                            duration_ms=duration_ms,
                            observed=observed,
                            expected=compiled_test["expected"],
                            query_id=query_id
                        )
                        session.add(test_record)

                        logger.info(
                            "Test executed successfully",
                            test_name=compiled_test["name"],
                            status=status,
                            duration_ms=duration_ms
                        )

                    except Exception as e:
                        test_end = datetime.utcnow()
                        duration_ms = int((test_end - test_start).total_seconds() * 1000)

                        logger.error(
                            "Test execution failed",
                            test_name=compiled_test["name"],
                            error=str(e)
                        )

                        # Create error test record
                        test_record = RunTest(
                            run_id=uuid.UUID(run_id),
                            name=compiled_test["name"],
                            type=compiled_test["type"],
                            status="error",
                            started_at=test_start,
                            finished_at=test_end,
                            duration_ms=duration_ms,
                            observed=None,
                            expected=compiled_test["expected"],
                            error_message=str(e)
                        )
                        session.add(test_record)

                # Update run record
                end_time = datetime.utcnow()
                total_duration_ms = int((end_time - start_time).total_seconds() * 1000)

                run_record = session.query(Run).filter(Run.id == run_id).first()
                if run_record:
                    run_record.status = "completed"
                    run_record.finished_at = end_time
                    run_record.duration_ms = total_duration_ms
                    run_record.query_ids = query_ids
                session.commit()

                # Generate run report for artifacts
                run_report = self._generate_run_report(run_record, session)

                # Store artifacts
                await artifact_service.store_run_report(run_id, run_report)

            logger.info(
                "Test execution completed",
                run_id=run_id,
                total_duration_ms=total_duration_ms,
                query_count=len(query_ids)
            )

        except Exception as e:
            logger.error("Test execution failed", run_id=run_id, exc_info=e)

            # Update run status to failed
            with db_manager.get_session() as session:
                run_record = session.query(Run).filter(Run.id == run_id).first()
                if run_record:
                    run_record.status = "failed"
                    run_record.finished_at = datetime.utcnow()
                    run_record.error_message = str(e)
                    session.commit()

            raise

        finally:
            # Clean up Snowflake connection
            if self.snowflake_connector:
                await self.snowflake_connector.disconnect()
                self.snowflake_connector = None

    def _evaluate_test_result(self, compiled_test: Dict[str, Any], result_rows: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """Evaluate test result against expected values."""
        test_type = compiled_test["type"]
        expected = compiled_test["expected"]

        if not result_rows:
            return "error", {"error": "No results returned"}

        if test_type == "row_count":
            row_count = result_rows[0].get("ROW_COUNT", 0)
            observed = {"row_count": row_count}

            min_rows = expected.get("min_rows", 0)
            max_rows = expected.get("max_rows")

            if row_count < min_rows:
                return "fail", observed
            if max_rows is not None and row_count > max_rows:
                return "fail", observed
            return "pass", observed

        elif test_type == "schema":
            columns = []
            for row in result_rows:
                columns.append({
                    "name": row.get("COLUMN_NAME"),
                    "type": row.get("DATA_TYPE"),
                    "nullable": row.get("IS_NULLABLE") == "YES"
                })

            observed = {"columns": columns}
            expected_columns = expected.get("columns", [])

            # Simple validation - check if expected columns exist
            if expected_columns:
                column_names = {col["name"] for col in columns}
                expected_names = {col.get("name") for col in expected_columns if col.get("name")}

                if not expected_names.issubset(column_names):
                    return "fail", observed

            return "pass", observed

        elif test_type == "null_check":
            null_count = result_rows[0].get("NULL_COUNT", 0)
            observed = {"null_count": null_count}
            expected_nulls = expected.get("null_count", 0)

            if null_count != expected_nulls:
                return "fail", observed
            return "pass", observed

        elif test_type == "duplicate_check":
            duplicate_count = len(result_rows) if result_rows else 0
            observed = {"duplicate_count": duplicate_count}
            expected_duplicates = expected.get("duplicate_count", 0)

            if duplicate_count != expected_duplicates:
                return "fail", observed
            return "pass", observed

        else:
            return "error", {"error": f"Unknown test type: {test_type}"}

    def _generate_run_report(self, run_record: Run, session: Session) -> Dict[str, Any]:
        """Generate comprehensive run report for artifact storage."""
        # Get all test results for this run
        test_results = session.query(RunTest).filter(RunTest.run_id == run_record.id).all()

        # Calculate summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t.status == "pass")
        failed_tests = sum(1 for t in test_results if t.status == "fail")
        error_tests = sum(1 for t in test_results if t.status == "error")

        # Build report
        report = {
            "run_id": str(run_record.id),
            "suite_name": run_record.suite_name,
            "status": run_record.status,
            "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
            "finished_at": run_record.finished_at.isoformat() if run_record.finished_at else None,
            "duration_ms": run_record.duration_ms,
            "bytes_scanned": run_record.bytes_scanned,
            "environment": run_record.environment,
            "connection": run_record.connection,
            "query_ids": run_record.query_ids or [],
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": [test.to_dict() for test in test_results],
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        return report

    async def get_run(self, run_id: str) -> Optional[RunSummary]:
        """Get run summary by ID."""
        db_manager = get_db_manager()
        try:
            with db_manager.get_session() as session:
                run_record = session.query(Run).filter(Run.id == run_id).first()
                if not run_record:
                    return None

                # Get test results
                test_results = session.query(RunTest).filter(RunTest.run_id == run_id).all()
                
                # Convert to RunSummary format
                return RunSummary(
                    run_id=str(run_record.id),
                    suite_name=run_record.suite_name,
                    status=run_record.status,
                    started_at=run_record.started_at,
                    finished_at=run_record.finished_at,
                    duration_ms=run_record.duration_ms or 0,
                    test_count=len(test_results),
                    passed_count=sum(1 for t in test_results if t.status == "pass"),
                    failed_count=sum(1 for t in test_results if t.status == "fail"),
                    error_count=sum(1 for t in test_results if t.status == "error"),
                    artifacts=[]  # Will be populated from artifact service
                )
        except Exception as e:
            logger.error("Failed to get run", run_id=run_id, exc_info=e)
            return None

    async def list_runs(self, request: RunListRequest) -> RunListResponse:
        """List runs with pagination."""
        db_manager = get_db_manager()
        try:
            with db_manager.get_session() as session:
                query = session.query(Run)
                
                # Apply filters
                if request.status:
                    query = query.filter(Run.status == request.status)
                if request.suite_name:
                    query = query.filter(Run.suite_name.contains(request.suite_name))
                
                # Apply pagination
                total = query.count()
                runs = query.order_by(Run.started_at.desc()).offset(request.offset).limit(request.limit).all()
                
                # Convert to summaries
                summaries = []
                for run in runs:
                    test_results = session.query(RunTest).filter(RunTest.run_id == run.id).all()
                    summary = RunSummary(
                        run_id=str(run.id),
                        suite_name=run.suite_name,
                        status=run.status,
                        started_at=run.started_at,
                        finished_at=run.finished_at,
                        duration_ms=run.duration_ms or 0,
                        test_count=len(test_results),
                        passed_count=sum(1 for t in test_results if t.status == "pass"),
                        failed_count=sum(1 for t in test_results if t.status == "fail"),
                        error_count=sum(1 for t in test_results if t.status == "error"),
                        artifacts=[]
                    )
                    summaries.append(summary)
                
                return RunListResponse(
                    runs=summaries,
                    total=total,
                    offset=request.offset,
                    limit=request.limit
                )
        except Exception as e:
            logger.error("Failed to list runs", exc_info=e)
            return RunListResponse(runs=[], total=0, offset=0, limit=request.limit)

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a running test suite."""
        db_manager = get_db_manager()
        try:
            with db_manager.get_session() as session:
                run_record = session.query(Run).filter(Run.id == run_id).first()
                if run_record and run_record.status == "running":
                    run_record.status = "cancelled"
                    run_record.finished_at = datetime.utcnow()
                    session.commit()
                    logger.info("Run cancelled", run_id=run_id)
                    return True
                return False
        except Exception as e:
            logger.error("Failed to cancel run", run_id=run_id, exc_info=e)
            return False

    async def get_run_prompts(self, run_id: str) -> List[str]:
        """Get AI prompts used in a run."""
        # Mock implementation for now
        return [
            "Generate SQL test for row count validation",
            "Create schema validation query for table structure"
        ]

# Global runner service instance
runner_service = RunnerService()