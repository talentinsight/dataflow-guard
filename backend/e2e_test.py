#!/usr/bin/env python3
"""
E2E Test Script for DataFlowGuard Demo
Akşam demo için Snowflake ile gerçek test
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dto_api.services.runner import runner_service
from dto_api.models.reports import RunRequest
from dto_api.db.models import init_database

async def main():
    print("🚀 DataFlowGuard E2E Test - Demo Hazırlığı")
    print("=" * 50)
    
    # Initialize database (use SQLite for demo)
    database_url = "sqlite:///./dto_demo.db"
    init_database(database_url)
    print(f"✅ Database initialized: {database_url}")
    
    # Check Snowflake credentials
    snowflake_config = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"), 
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    }
    
    missing_config = [k for k, v in snowflake_config.items() if not v]
    if missing_config:
        print(f"❌ Missing Snowflake config: {missing_config}")
        print("\nLütfen şu environment variable'ları ayarlayın:")
        for key in missing_config:
            print(f"export SNOWFLAKE_{key.upper()}=your_value")
        return
    
    print(f"✅ Snowflake config: {snowflake_config['account']}/{snowflake_config['database']}")
    
    # Create test request
    test_request = RunRequest(
        suite_id="demo-suite",
        dry_run=False,
        connection_override="snowflake",
        test_filter=None  # Run all tests
    )
    
    print("\n🧪 Starting E2E Test Execution...")
    print(f"Suite ID: {test_request.suite_id}")
    print(f"Dry Run: {test_request.dry_run}")
    
    try:
        # Execute test suite
        response = await runner_service.execute_suite(test_request)
        
        print(f"\n✅ Test execution started!")
        print(f"Run ID: {response.run_id}")
        print(f"Status: {response.status}")
        print(f"Estimated Duration: {response.estimated_duration_seconds}s")
        
        if response.status == "running":
            print("\n⏳ Waiting for test completion...")
            
            # Poll for completion
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(5)
                wait_time += 5
                
                run_summary = await runner_service.get_run(response.run_id)
                if run_summary:
                    print(f"Status: {run_summary.status} | "
                          f"Tests: {run_summary.test_count} | "
                          f"Passed: {run_summary.passed_count} | "
                          f"Failed: {run_summary.failed_count} | "
                          f"Errors: {run_summary.error_count}")
                    
                    if run_summary.status in ["completed", "failed", "cancelled"]:
                        break
            
            # Final results
            final_summary = await runner_service.get_run(response.run_id)
            if final_summary:
                print(f"\n🎯 Final Results:")
                print(f"Status: {final_summary.status}")
                print(f"Duration: {final_summary.duration_ms}ms")
                print(f"Total Tests: {final_summary.test_count}")
                print(f"✅ Passed: {final_summary.passed_count}")
                print(f"❌ Failed: {final_summary.failed_count}")
                print(f"⚠️  Errors: {final_summary.error_count}")
                
                success_rate = (final_summary.passed_count / final_summary.test_count * 100) if final_summary.test_count > 0 else 0
                print(f"Success Rate: {success_rate:.1f}%")
                
                if final_summary.status == "completed" and final_summary.failed_count == 0:
                    print("\n🎉 E2E Test BAŞARILI! Demo için hazır!")
                else:
                    print(f"\n⚠️  E2E Test tamamlandı ama bazı testler başarısız.")
                    
        else:
            print(f"\n✅ Dry run completed successfully!")
            
    except Exception as e:
        print(f"\n❌ E2E Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n📊 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
