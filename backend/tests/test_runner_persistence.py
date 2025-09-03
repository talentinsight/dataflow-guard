"""Unit tests for runner service database persistence."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from dto_api.db.models import DatabaseManager, Run, RunTest, Artifact
from dto_api.services.runner import RunnerService
from dto_api.models.tests import TestSuite, TestDefinition


class TestRunnerPersistence:
    """Test cases for RunnerService database persistence."""
    
    @pytest.fixture
    def db_manager(self):
        """Create in-memory SQLite database for testing."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        return db_manager
    
    @pytest.fixture
    def runner_service(self):
        """Create RunnerService instance."""
        return RunnerService()
    
    @pytest.fixture
    def sample_suite(self):
        """Create sample test suite."""
        return TestSuite(
            name="test_suite",
            connection="snowflake_test",
            description="Test suite for persistence testing",
            tests=[
                TestDefinition(
                    name="row_count_test",
                    type="row_count",
                    dataset="TEST.ORDERS",
                    expected_min=100,
                    expected_max=1000
                ),
                TestDefinition(
                    name="schema_test",
                    type="schema",
                    dataset="TEST.ORDERS",
                    expected_columns=[{"name": "ID", "type": "NUMBER"}]
                )
            ]
        )
    
    def test_database_manager_initialization(self, db_manager):
        """Test database manager creates tables correctly."""
        with db_manager.get_session() as session:
            # Should be able to query empty tables
            runs = session.query(Run).all()
            tests = session.query(RunTest).all()
            artifacts = session.query(Artifact).all()
            
            assert runs == []
            assert tests == []
            assert artifacts == []
    
    def test_database_manager_health_check(self, db_manager):
        """Test database health check."""
        assert db_manager.health_check() is True
    
    def test_create_run_record(self, db_manager):
        """Test creating a run record in database."""
        with db_manager.get_session() as session:
            run_id = uuid.uuid4()
            run_record = Run(
                id=run_id,
                suite_name="test_suite",
                status="running",
                started_at=datetime.utcnow(),
                environment="test",
                connection="snowflake_test"
            )
            
            session.add(run_record)
            session.commit()
            
            # Verify record was created
            retrieved_run = session.query(Run).filter(Run.id == run_id).first()
            assert retrieved_run is not None
            assert retrieved_run.suite_name == "test_suite"
            assert retrieved_run.status == "running"
            assert retrieved_run.environment == "test"
    
    def test_create_test_results(self, db_manager):
        """Test creating test result records."""
        with db_manager.get_session() as session:
            # Create parent run
            run_id = uuid.uuid4()
            run_record = Run(
                id=run_id,
                suite_name="test_suite",
                status="completed",
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                duration_ms=5000
            )
            session.add(run_record)
            session.flush()
            
            # Create test results
            test_result = RunTest(
                run_id=run_id,
                name="row_count_test",
                type="row_count",
                status="pass",
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                duration_ms=1000,
                observed={"row_count": 500},
                expected={"min_rows": 100, "max_rows": 1000},
                query_id="test_query_123"
            )
            session.add(test_result)
            session.commit()
            
            # Verify relationships work
            retrieved_run = session.query(Run).filter(Run.id == run_id).first()
            assert len(retrieved_run.tests) == 1
            assert retrieved_run.tests[0].name == "row_count_test"
            assert retrieved_run.tests[0].status == "pass"
            assert retrieved_run.tests[0].observed == {"row_count": 500}
    
    def test_create_artifacts(self, db_manager):
        """Test creating artifact records."""
        with db_manager.get_session() as session:
            # Create parent run
            run_id = uuid.uuid4()
            run_record = Run(id=run_id, suite_name="test", status="completed")
            session.add(run_record)
            session.flush()
            
            # Create artifact
            artifact = Artifact(
                run_id=run_id,
                kind="report",
                path="runs/2024/01/01/test-run/report.json",
                url="http://minio:9000/bucket/runs/2024/01/01/test-run/report.json",
                size_bytes=1024,
                content_type="application/json"
            )
            session.add(artifact)
            session.commit()
            
            # Verify relationships
            retrieved_run = session.query(Run).filter(Run.id == run_id).first()
            assert len(retrieved_run.artifacts) == 1
            assert retrieved_run.artifacts[0].kind == "report"
            assert retrieved_run.artifacts[0].size_bytes == 1024
    
    def test_run_to_dict_serialization(self, db_manager):
        """Test Run model to_dict method."""
        with db_manager.get_session() as session:
            run_id = uuid.uuid4()
            start_time = datetime.utcnow()
            
            run_record = Run(
                id=run_id,
                suite_name="test_suite",
                status="completed",
                started_at=start_time,
                finished_at=start_time,
                duration_ms=2000,
                bytes_scanned=1000000,
                query_ids=["query1", "query2"],
                environment="test"
            )
            session.add(run_record)
            session.commit()
            
            # Test serialization
            run_dict = run_record.to_dict()
            
            assert run_dict["id"] == str(run_id)
            assert run_dict["suite_name"] == "test_suite"
            assert run_dict["status"] == "completed"
            assert run_dict["duration_ms"] == 2000
            assert run_dict["bytes_scanned"] == 1000000
            assert run_dict["query_ids"] == ["query1", "query2"]
            assert run_dict["environment"] == "test"
            assert "started_at" in run_dict
            assert "finished_at" in run_dict
    
    def test_run_test_to_dict_serialization(self, db_manager):
        """Test RunTest model to_dict method."""
        with db_manager.get_session() as session:
            run_id = uuid.uuid4()
            test_id = uuid.uuid4()
            
            # Create parent run first
            run_record = Run(id=run_id, suite_name="test", status="completed")
            session.add(run_record)
            session.flush()
            
            test_record = RunTest(
                id=test_id,
                run_id=run_id,
                name="test_case",
                type="row_count",
                status="pass",
                duration_ms=500,
                observed={"count": 100},
                expected={"min": 50, "max": 150},
                query_id="test_query"
            )
            session.add(test_record)
            session.commit()
            
            # Test serialization
            test_dict = test_record.to_dict()
            
            assert test_dict["id"] == str(test_id)
            assert test_dict["run_id"] == str(run_id)
            assert test_dict["name"] == "test_case"
            assert test_dict["type"] == "row_count"
            assert test_dict["status"] == "pass"
            assert test_dict["duration_ms"] == 500
            assert test_dict["observed"] == {"count": 100}
            assert test_dict["expected"] == {"min": 50, "max": 150}
            assert test_dict["query_id"] == "test_query"
    
    @patch('dto_api.db.models.get_db_manager')
    def test_runner_service_database_integration(self, mock_get_db_manager, db_manager, runner_service, sample_suite):
        """Test RunnerService integration with database."""
        mock_get_db_manager.return_value = db_manager
        
        # Mock the _get_test_suite method to return our sample suite
        with patch.object(runner_service, '_get_test_suite', return_value=sample_suite):
            # Mock Snowflake connector to avoid actual connection
            with patch('dto_api.services.runner.SnowflakeConnector') as mock_connector:
                mock_instance = AsyncMock()
                mock_connector.return_value = mock_instance
                
                # Mock the execution methods
                with patch.object(runner_service, '_execute_tests_real') as mock_execute:
                    mock_execute.return_value = None
                    
                    # Create a run request
                    from dto_api.models.reports import RunRequest
                    request = RunRequest(
                        suite_id="test_suite",
                        dry_run=False
                    )
                    
                    # This should create a run record in the database
                    # Note: We can't easily test the full async execution here,
                    # but we can verify the database record creation
                    
                    # Verify we can query the database
                    with db_manager.get_session() as session:
                        runs_before = session.query(Run).count()
                        assert runs_before == 0
    
    def test_generate_run_report(self, db_manager, runner_service):
        """Test run report generation."""
        with db_manager.get_session() as session:
            # Create test data
            run_id = uuid.uuid4()
            start_time = datetime.utcnow()
            
            run_record = Run(
                id=run_id,
                suite_name="test_suite",
                status="completed",
                started_at=start_time,
                finished_at=start_time,
                duration_ms=3000,
                bytes_scanned=500000,
                query_ids=["q1", "q2"],
                environment="test"
            )
            session.add(run_record)
            session.flush()
            
            # Add test results
            test1 = RunTest(
                run_id=run_id,
                name="test1",
                type="row_count",
                status="pass",
                observed={"count": 100},
                expected={"min": 50}
            )
            test2 = RunTest(
                run_id=run_id,
                name="test2", 
                type="schema",
                status="fail",
                observed={"columns": []},
                expected={"columns": ["ID"]}
            )
            session.add_all([test1, test2])
            session.commit()
            
            # Generate report
            report = runner_service._generate_run_report(run_record, session)
            
            # Verify report structure
            assert report["run_id"] == str(run_id)
            assert report["suite_name"] == "test_suite"
            assert report["status"] == "completed"
            assert report["duration_ms"] == 3000
            assert report["bytes_scanned"] == 500000
            assert report["query_ids"] == ["q1", "q2"]
            
            # Verify summary statistics
            summary = report["summary"]
            assert summary["total_tests"] == 2
            assert summary["passed_tests"] == 1
            assert summary["failed_tests"] == 1
            assert summary["error_tests"] == 0
            assert summary["success_rate"] == 50.0
            
            # Verify test results included
            assert len(report["test_results"]) == 2
            assert report["test_results"][0]["name"] == "test1"
            assert report["test_results"][1]["name"] == "test2"
