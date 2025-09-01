"""Real test runner service with Snowflake execution and security controls."""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import structlog

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
from dto_api.policies.pii_redaction import PIIRedactionPolicy

logger = structlog.get_logger()


class RunnerService:
    """Real test runner service for executing test suites with Snowflake."""
    
    def __init__(self):
        # TODO: Initialize database connection and artifact storage
        self._runs: Dict[str, RunSummary] = {}
        self._results: Dict[str, List[TestResult]] = {}
        self.artifacts_path = Path("artifacts")
        self.artifacts_path.mkdir(exist_ok=True)
        
        self.ai_adapter = AIAdapterInterface()
        self.pii_policy = PIIRedactionPolicy(enabled=True)
    
    async def execute_suite(self, request: RunRequest) -> RunResponse:
        """Execute a test suite with real Snowflake connector."""
        try:
            run_id = f"{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}-{str(uuid.uuid4())[:8]}"
            
            logger.info(
                "Starting real test suite execution",
                run_id=run_id,
                suite_id=request.suite_id,
                dry_run=request.dry_run
            )
            
            # Get test suite (mock for now)
            suite = await self._get_test_suite(request.suite_id)
            if not suite:
                raise ValueError(f"Test suite '{request.suite_id}' not found")
            
            # Create run summary
            run_summary = RunSummary(
                run_id=run_id,
                suite_name=suite.name,
                status="running",
                total_tests=len(suite.tests),
                started_at=datetime.utcnow(),
                environment="dev",
                connection=request.connection_override or suite.connection
            )
            
            # Store run (in production, this would be in database)
            self._runs[run_id] = run_summary
            
            if not request.dry_run:
                # Start background execution
                await self._execute_tests_real(run_id, suite, request)
            else:
                # For dry run, validate and return
                await self._validate_tests(suite)
                run_summary.status = "completed"
                run_summary.ended_at = datetime.utcnow()
                run_summary.execution_time_ms = 100
            
            estimated_duration = 300 if not request.dry_run else 5
            
            return RunResponse(
                run_id=run_id,
                status=run_summary.status,
                estimated_duration_seconds=estimated_duration
            )
            
        except Exception as e:
            logger.error("Failed to start test execution", exc_info=e)
            raise
    
    async def _get_test_suite(self, suite_id: str) -> Optional[TestSuite]:
        """Get test suite by ID (mock implementation)."""
        # TODO: Implement actual suite retrieval from database
        if suite_id == "orders_basic":
            return TestSuite(
                name="orders_basic",
                connection="snowflake_prod",
                description="Basic data quality tests for orders pipeline",
                tests=[
                    TestDefinition(
                        name="pk_uniqueness_orders",
                        type="uniqueness",
                        dataset="PROD_DB.RAW.ORDERS",
                        keys=["ORDER_ID"],
                        tolerance={"dup_rows": 0},
                        severity="blocker",
                        gate="fail"
                    ),
                    TestDefinition(
                        name="not_null_order_id",
                        type="not_null",
                        dataset="PROD_DB.RAW.ORDERS",
                        keys=["ORDER_ID"],
                        severity="blocker",
                        gate="fail"
                    ),
                    TestDefinition(
                        name="freshness_orders",
                        type="freshness",
                        dataset="PROD_DB.RAW.ORDERS",
                        window={"last_hours": 24},
                        severity="major",
                        gate="warn"
                    )
                ],
                tags=["orders", "basic"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        return None
    
    async def _validate_tests(self, suite: TestSuite) -> None:
        """Validate test suite without execution."""
        for test in suite.tests:
            # Compile test to SQL
            compile_request = {
                "expression": self._generate_test_expression(test),
                "dataset": test.dataset,
                "test_type": test.type
            }
            
            try:
                result = await self.ai_adapter.compile_expression(compile_request)
                logger.info(
                    "Test validation passed",
                    test_name=test.name,
                    confidence=result.confidence
                )
            except Exception as e:
                logger.error(
                    "Test validation failed",
                    test_name=test.name,
                    error=str(e)
                )
                raise ValueError(f"Test '{test.name}' validation failed: {e}")
    
    def _generate_test_expression(self, test: TestDefinition) -> str:
        """Generate natural language expression for test compilation."""
        if test.type == "uniqueness":
            keys_str = ", ".join(test.keys or [])
            return f"{keys_str} should be unique"
        elif test.type == "not_null":
            keys_str = ", ".join(test.keys or [])
            return f"{keys_str} should not be null"
        elif test.type == "freshness":
            hours = test.window.last_hours if test.window else 24
            return f"data should be fresh within {hours} hours"
        elif test.type == "rule" and test.expression:
            return test.expression
        else:
            return f"validate {test.type} for {test.dataset}"
    
    async def _execute_tests_real(self, run_id: str, suite: TestSuite, request: RunRequest) -> None:
        """Execute tests with real Snowflake connector."""
        try:
            logger.info("Starting real test execution", run_id=run_id, suite_name=suite.name)
            
            # Initialize Snowflake connector
            connector = SnowflakeConnector()
            test_results = []
            
            for test in suite.tests:
                if request.test_filter and test.name not in request.test_filter:
                    continue
                
                try:
                    result = await self._execute_single_test(test, connector, run_id)
                    test_results.append(result)
                    
                except Exception as e:
                    logger.error(
                        "Test execution failed",
                        test_name=test.name,
                        run_id=run_id,
                        error=str(e)
                    )
                    
                    # Create error result
                    error_result = TestResult(
                        test_name=test.name,
                        status="error",
                        metrics={},
                        error_message=str(e),
                        started_at=datetime.utcnow(),
                        ended_at=datetime.utcnow(),
                        execution_time_ms=0
                    )
                    test_results.append(error_result)
            
            # Disconnect from Snowflake
            await connector.disconnect()
            
            # Store results
            self._results[run_id] = test_results
            
            # Update run summary
            run_summary = self._runs[run_id]
            run_summary.status = "completed"
            run_summary.ended_at = datetime.utcnow()
            run_summary.execution_time_ms = int((run_summary.ended_at - run_summary.started_at).total_seconds() * 1000)
            
            # Count results by status
            run_summary.passed_tests = sum(1 for r in test_results if r.status == "pass")
            run_summary.failed_tests = sum(1 for r in test_results if r.status == "fail")
            run_summary.error_tests = sum(1 for r in test_results if r.status == "error")
            run_summary.skipped_tests = sum(1 for r in test_results if r.status == "skip")
            
            # Generate artifacts
            artifacts = await self._generate_artifacts(run_id, run_summary, test_results)
            run_summary.artifacts = artifacts
            
            logger.info(
                "Real test execution completed",
                run_id=run_id,
                status=run_summary.status,
                passed=run_summary.passed_tests,
                failed=run_summary.failed_tests,
                errors=run_summary.error_tests
            )
            
        except Exception as e:
            logger.error("Real test execution failed", run_id=run_id, exc_info=e)
            # Update run status to failed
            if run_id in self._runs:
                self._runs[run_id].status = "failed"
                self._runs[run_id].ended_at = datetime.utcnow()
    
    async def _execute_single_test(
        self, 
        test: TestDefinition, 
        connector: SnowflakeConnector,
        run_id: str
    ) -> TestResult:
        """Execute a single test with Snowflake."""
        start_time = datetime.utcnow()
        
        try:
            logger.info("Executing test", test_name=test.name, test_type=test.type)
            
            # Generate SQL for the test
            sql = await self._generate_test_sql(test)
            
            # Step 1: Validate SQL (built into connector)
            # Step 2: Run EXPLAIN
            explain_result = await connector.explain(sql)
            
            logger.info(
                "EXPLAIN completed",
                test_name=test.name,
                plan_hash=explain_result['plan_hash'],
                estimated_bytes=explain_result.get('estimated_bytes', 0)
            )
            
            # Step 3: Execute SELECT
            select_result = await connector.select(sql, limit=1000)
            
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Analyze results based on test type
            status, violations, metrics = self._analyze_test_result(test, select_result)
            
            # Create sample rows URI if there are violations
            sample_rows_uri = None
            if violations > 0:
                sample_rows_uri = await self._store_sample_rows(
                    run_id, test.name, select_result['rows']
                )
            
            logger.info(
                "Test execution completed",
                test_name=test.name,
                status=status,
                violations=violations,
                query_id=select_result['query_id'],
                bytes_scanned=select_result['stats'].get('bytes_scanned', 0)
            )
            
            return TestResult(
                test_name=test.name,
                status=status,
                metrics={
                    **metrics,
                    'query_id': select_result['query_id'],
                    'bytes_scanned': select_result['stats'].get('bytes_scanned', 0),
                    'plan_hash': explain_result['plan_hash']
                },
                violations=violations,
                sample_rows_uri=sample_rows_uri,
                started_at=start_time,
                ended_at=end_time,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error("Test execution failed", test_name=test.name, error=str(e))
            
            return TestResult(
                test_name=test.name,
                status="error",
                metrics={},
                error_message=str(e),
                started_at=start_time,
                ended_at=end_time,
                execution_time_ms=execution_time_ms
            )
    
    async def _generate_test_sql(self, test: TestDefinition) -> str:
        """Generate SQL for a test definition."""
        if test.type == "uniqueness":
            keys = ", ".join(test.keys or [])
            return f"""
            SELECT {keys}, COUNT(*) as duplicate_count
            FROM {test.dataset}
            GROUP BY {keys}
            HAVING COUNT(*) > 1
            """
        
        elif test.type == "not_null":
            key = test.keys[0] if test.keys else "id"
            return f"""
            SELECT COUNT(*) as null_count
            FROM {test.dataset}
            WHERE {key} IS NULL
            """
        
        elif test.type == "freshness":
            # Assume there's a timestamp column (would be configured)
            timestamp_col = "ORDER_TS"  # This should come from test config
            hours = test.window.last_hours if test.window else 24
            return f"""
            SELECT 
                MAX({timestamp_col}) as max_timestamp,
                CURRENT_TIMESTAMP() as current_timestamp,
                DATEDIFF('hour', MAX({timestamp_col}), CURRENT_TIMESTAMP()) as hours_lag
            FROM {test.dataset}
            """
        
        elif test.type == "rule" and test.expression:
            # For business rules, compile the expression
            compile_request = {
                "expression": test.expression,
                "dataset": test.dataset,
                "test_type": test.type
            }
            result = await self.ai_adapter.compile_expression(compile_request)
            return result.sql_preview
        
        else:
            raise ValueError(f"Unsupported test type: {test.type}")
    
    def _analyze_test_result(
        self, 
        test: TestDefinition, 
        result: Dict[str, Any]
    ) -> tuple[str, int, Dict[str, Any]]:
        """Analyze test result and determine pass/fail status."""
        rows = result['rows']
        stats = result['stats']
        
        if test.type == "uniqueness":
            violations = len(rows)  # Each row represents a duplicate group
            total_duplicates = sum(row.get('DUPLICATE_COUNT', 0) for row in rows)
            
            tolerance = test.tolerance.dup_rows if test.tolerance else 0
            status = "pass" if violations <= tolerance else "fail"
            
            metrics = {
                'duplicate_groups': violations,
                'total_duplicates': total_duplicates,
                'tolerance': tolerance
            }
            
        elif test.type == "not_null":
            null_count = rows[0].get('NULL_COUNT', 0) if rows else 0
            violations = null_count
            status = "pass" if violations == 0 else "fail"
            
            metrics = {
                'null_count': null_count,
                'total_rows': stats.get('rows', 0)
            }
            
        elif test.type == "freshness":
            if rows:
                hours_lag = rows[0].get('HOURS_LAG', 0)
                max_hours = test.window.last_hours if test.window else 24
                
                violations = max(0, hours_lag - max_hours)
                status = "pass" if hours_lag <= max_hours else "fail"
                
                metrics = {
                    'hours_lag': hours_lag,
                    'max_hours_allowed': max_hours,
                    'max_timestamp': rows[0].get('MAX_TIMESTAMP')
                }
            else:
                violations = 1
                status = "fail"
                metrics = {'error': 'No data found'}
        
        else:
            # Default analysis for other test types
            violations = len(rows)
            status = "pass" if violations == 0 else "fail"
            metrics = {'violation_count': violations}
        
        return status, violations, metrics
    
    async def _store_sample_rows(
        self, 
        run_id: str, 
        test_name: str, 
        rows: List[Dict[str, Any]]
    ) -> str:
        """Store sample violation rows and return URI."""
        samples_dir = self.artifacts_path / "runs" / run_id / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)
        
        # Apply PII redaction
        redacted_rows = self.pii_policy.redact_sample_data(rows)
        
        sample_data = {
            'test_name': test_name,
            'run_id': run_id,
            'sample_count': len(redacted_rows),
            'sample_rows': redacted_rows[:100]  # Limit to 100 samples
        }
        
        sample_path = samples_dir / f"{test_name}_violations.json"
        sample_path.write_text(json.dumps(sample_data, indent=2, default=str))
        
        return f"artifact://runs/{run_id}/samples/{test_name}_violations.json"
    
    async def _generate_artifacts(
        self, 
        run_id: str, 
        run_summary: RunSummary, 
        test_results: List[TestResult]
    ) -> Dict[str, str]:
        """Generate HTML and JSONL artifacts with real data."""
        run_dir = self.artifacts_path / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_content = self._generate_html_report(run_summary, test_results)
        html_path = run_dir / "report.html"
        html_path.write_text(html_content)
        
        # Generate JSONL results
        jsonl_content = self._generate_jsonl_report(run_id, run_summary, test_results)
        jsonl_path = run_dir / "results.jsonl"
        jsonl_path.write_text(jsonl_content)
        
        return {
            "html_report": f"artifact://runs/{run_id}/report.html",
            "jsonl_results": f"artifact://runs/{run_id}/results.jsonl",
            "samples_dir": f"artifact://runs/{run_id}/samples/"
        }
    
    def _generate_html_report(self, run_summary: RunSummary, test_results: List[TestResult]) -> str:
        """Generate enhanced HTML report with real execution data."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>DTO Test Report - {run_summary.run_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: #e9f4ff; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric.failed {{ background: #ffe9e9; }}
        .metric.passed {{ background: #e9ffe9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .status-pass {{ color: green; font-weight: bold; }}
        .status-fail {{ color: red; font-weight: bold; }}
        .status-error {{ color: orange; font-weight: bold; }}
        .query-info {{ font-size: 0.8em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>DTO Test Report</h1>
        <p><strong>Run ID:</strong> {run_summary.run_id}</p>
        <p><strong>Suite:</strong> {run_summary.suite_name}</p>
        <p><strong>Status:</strong> {run_summary.status}</p>
        <p><strong>Connection:</strong> {run_summary.connection}</p>
        <p><strong>Executed:</strong> {run_summary.started_at.isoformat()}</p>
        <p><strong>Duration:</strong> {run_summary.execution_time_ms}ms</p>
    </div>
    
    <div class="summary">
        <div class="metric passed">
            <h3>{run_summary.passed_tests}</h3>
            <p>Passed</p>
        </div>
        <div class="metric failed">
            <h3>{run_summary.failed_tests}</h3>
            <p>Failed</p>
        </div>
        <div class="metric">
            <h3>{run_summary.error_tests}</h3>
            <p>Errors</p>
        </div>
        <div class="metric">
            <h3>{run_summary.total_tests}</h3>
            <p>Total</p>
        </div>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Violations</th>
                <th>Duration (ms)</th>
                <th>Query Info</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for result in test_results:
            status_class = f"status-{result.status}"
            violations = result.violations or 0
            query_id = result.metrics.get('query_id', 'N/A')
            bytes_scanned = result.metrics.get('bytes_scanned', 0)
            
            html += f"""
            <tr>
                <td>{result.test_name}</td>
                <td class="{status_class}">{result.status.upper()}</td>
                <td>{violations}</td>
                <td>{result.execution_time_ms}</td>
                <td class="query-info">
                    Query ID: {query_id}<br/>
                    Bytes Scanned: {bytes_scanned:,}
                </td>
                <td>{result.sample_rows_uri or result.error_message or 'N/A'}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <div class="footer">
        <p><em>Generated by DataFlowGuard DTO - Zero-SQL Data Testing Framework</em></p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_jsonl_report(
        self, 
        run_id: str, 
        run_summary: RunSummary, 
        test_results: List[TestResult]
    ) -> str:
        """Generate JSONL report with real execution data."""
        lines = []
        
        for result in test_results:
            record = ReportRecord(
                run_id=run_id,
                suite=run_summary.suite_name,
                test=result.test_name,
                status=result.status,
                metrics=result.metrics,
                sample_rows_uri=result.sample_rows_uri,
                started_at=result.started_at,
                ended_at=result.ended_at,
                ai={
                    "model": "local-llm:Q4_K_M",
                    "seed": 42,
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "prompts_uri": f"artifact://runs/{run_id}/ai/prompts.jsonl"
                }
            )
            lines.append(record.model_dump_json())
        
        return "\n".join(lines)
    
    # Keep existing methods from stub implementation
    async def list_runs(self, request: RunListRequest) -> RunListResponse:
        """List runs with filters."""
        runs = list(self._runs.values())
        
        # Apply filters
        if request.status:
            runs = [r for r in runs if r.status == request.status]
        if request.suite:
            runs = [r for r in runs if request.suite.lower() in r.suite_name.lower()]
        if request.date_from:
            runs = [r for r in runs if r.started_at >= request.date_from]
        if request.date_to:
            runs = [r for r in runs if r.started_at <= request.date_to]
        
        # Sort by start time (newest first)
        runs.sort(key=lambda x: x.started_at, reverse=True)
        
        # Apply pagination
        total = len(runs)
        paginated = runs[request.offset:request.offset + request.limit]
        
        return RunListResponse(
            runs=paginated,
            total=total,
            limit=request.limit,
            offset=request.offset
        )
    
    async def get_run_summary(self, run_id: str) -> Optional[RunSummary]:
        """Get run summary by ID."""
        return self._runs.get(run_id)
    
    async def get_run_results(
        self, 
        run_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[TestResult]:
        """Get test results for a run."""
        results = self._results.get(run_id, [])
        return results[offset:offset + limit]
    
    async def get_run_artifacts(self, run_id: str) -> Optional[Dict[str, str]]:
        """Get artifact URIs for a run."""
        run_summary = self._runs.get(run_id)
        return run_summary.artifacts if run_summary else None
    
    async def get_ai_prompts(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get AI prompts for a run (redacted)."""
        return {
            "prompts_uri": f"artifact://runs/{run_id}/ai/prompts.jsonl",
            "total_prompts": 3,
            "redacted": True,
            "note": "Prompts are redacted for privacy. Full logs available to admins."
        }
    
    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a running test suite."""
        run_summary = self._runs.get(run_id)
        if run_summary and run_summary.status == "running":
            run_summary.status = "cancelled"
            run_summary.ended_at = datetime.utcnow()
            return True
        return False
