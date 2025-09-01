"""DTO CLI main entry point."""

import json
import sys
from pathlib import Path
from typing import Optional, List

import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="dto",
    help="Data Testing Orchestrator CLI - Zero-SQL data testing framework",
    add_completion=False
)

console = Console()


# Global options
class GlobalOptions:
    def __init__(self):
        self.api_url: str = "http://localhost:8000/api/v1"
        self.verbose: bool = False


global_options = GlobalOptions()


@app.callback()
def main(
    api_url: str = typer.Option(
        "http://localhost:8000/api/v1",
        "--api-url",
        help="DTO API base URL"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    """Data Testing Orchestrator CLI."""
    global_options.api_url = api_url
    global_options.verbose = verbose


@app.command()
def health():
    """Check API health status."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{global_options.api_url}/healthz")
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"✅ API is healthy (v{data['version']})", style="green")
                if global_options.verbose:
                    console.print(JSON(json.dumps(data, indent=2)))
            else:
                console.print(f"❌ API health check failed: {response.status_code}", style="red")
                sys.exit(1)
                
    except Exception as e:
        console.print(f"❌ Failed to connect to API: {e}", style="red")
        sys.exit(1)


@app.command()
def import_catalog(
    file_path: Path = typer.Argument(..., help="Path to catalog file"),
    source_type: str = typer.Option(
        "catalog_package",
        "--source-type",
        help="Source type: catalog_package, dbt_manifest, dbt_catalog"
    ),
    environment: str = typer.Option("dev", "--env", help="Target environment")
):
    """Import catalog from file."""
    try:
        if not file_path.exists():
            console.print(f"❌ File not found: {file_path}", style="red")
            sys.exit(1)
        
        # Read catalog file
        with open(file_path) as f:
            catalog_data = json.load(f)
        
        # Import via API
        with httpx.Client() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Importing catalog...", total=None)
                
                response = client.post(
                    f"{global_options.api_url}/catalog/import",
                    json={
                        "source_type": source_type,
                        "data": catalog_data,
                        "environment": environment
                    },
                    timeout=60.0
                )
                
                progress.remove_task(task)
        
        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ Catalog imported successfully", style="green")
            console.print(f"   Catalog ID: {result['catalog_id']}")
            console.print(f"   Datasets imported: {result['datasets_imported']}")
            
            if result.get('warnings'):
                console.print("⚠️  Warnings:", style="yellow")
                for warning in result['warnings']:
                    console.print(f"   - {warning}")
        else:
            console.print(f"❌ Import failed: {response.status_code}", style="red")
            if global_options.verbose:
                console.print(response.text)
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Import failed: {e}", style="red")
        sys.exit(1)


@app.command()
def propose(
    datasets: List[str] = typer.Argument(..., help="Dataset names (schema.table)"),
    catalog_id: str = typer.Option(..., "--catalog-id", help="Catalog ID"),
    profile: str = typer.Option("standard", "--profile", help="Test profile: smoke, standard, deep, custom"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for proposals")
):
    """Propose tests for datasets using AI."""
    try:
        with httpx.Client() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating test proposals...", total=None)
                
                response = client.post(
                    f"{global_options.api_url}/tests/propose",
                    json={
                        "datasets": datasets,
                        "catalog_id": catalog_id,
                        "profile": profile
                    },
                    timeout=120.0
                )
                
                progress.remove_task(task)
        
        if response.status_code == 200:
            result = response.json()
            
            console.print(f"✅ Generated {result['total_proposed']} test proposals", style="green")
            console.print(f"   Auto-approvable: {result['auto_approvable_count']}")
            
            # Display proposals in table
            table = Table(title="Test Proposals")
            table.add_column("Test Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Dataset", style="green")
            table.add_column("Confidence", style="yellow")
            table.add_column("Auto-Approve", style="blue")
            
            for proposal in result['proposals']:
                test_def = proposal['test_def']
                table.add_row(
                    test_def['name'],
                    test_def['type'],
                    test_def['dataset'],
                    f"{proposal['confidence']:.2f}",
                    "✅" if proposal['auto_approvable'] else "❌"
                )
            
            console.print(table)
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                console.print(f"💾 Proposals saved to {output_file}")
                
        else:
            console.print(f"❌ Proposal failed: {response.status_code}", style="red")
            if global_options.verbose:
                console.print(response.text)
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Proposal failed: {e}", style="red")
        sys.exit(1)


@app.command()
def compile(
    expression: str = typer.Argument(..., help="Natural language or formula expression"),
    dataset: str = typer.Option(..., "--dataset", help="Target dataset (schema.table)"),
    test_type: Optional[str] = typer.Option(None, "--type", help="Test type hint"),
    show_sql: bool = typer.Option(False, "--show-sql", help="Show generated SQL")
):
    """Compile expression to IR and SQL."""
    try:
        with httpx.Client() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Compiling expression...", total=None)
                
                payload = {
                    "expression": expression,
                    "dataset": dataset
                }
                if test_type:
                    payload["test_type"] = test_type
                
                response = client.post(
                    f"{global_options.api_url}/tests/compile",
                    json=payload,
                    timeout=60.0
                )
                
                progress.remove_task(task)
        
        if response.status_code == 200:
            result = response.json()
            
            console.print(f"✅ Compilation successful (confidence: {result['confidence']:.2f})", style="green")
            
            # Show IR
            console.print("\n📋 Generated IR:", style="bold")
            console.print(JSON(json.dumps(result['ir'], indent=2)))
            
            # Show SQL if requested
            if show_sql:
                console.print("\n🔍 Generated SQL:", style="bold")
                console.print(result['sql_preview'], style="dim")
            
            # Show warnings
            if result.get('warnings'):
                console.print("\n⚠️  Warnings:", style="yellow")
                for warning in result['warnings']:
                    console.print(f"   - {warning}")
                    
        else:
            console.print(f"❌ Compilation failed: {response.status_code}", style="red")
            if global_options.verbose:
                console.print(response.text)
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Compilation failed: {e}", style="red")
        sys.exit(1)


@app.command()
def run(
    suite_id: str = typer.Argument(..., help="Test suite ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, don't execute"),
    budget: Optional[int] = typer.Option(None, "--budget", help="Time budget in seconds"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow run progress")
):
    """Execute a test suite."""
    try:
        with httpx.Client() as client:
            # Start run
            payload = {
                "suite_id": suite_id,
                "dry_run": dry_run
            }
            if budget:
                payload["budget_seconds"] = budget
            
            response = client.post(
                f"{global_options.api_url}/suites/{suite_id}/run",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                console.print(f"❌ Failed to start run: {response.status_code}", style="red")
                if global_options.verbose:
                    console.print(response.text)
                sys.exit(1)
            
            result = response.json()
            run_id = result['run_id']
            
            console.print(f"🚀 Started run: {run_id}", style="green")
            if dry_run:
                console.print("   Mode: Dry run (validation only)")
            
            # Follow progress if requested
            if follow and not dry_run:
                _follow_run_progress(client, run_id)
            else:
                console.print(f"   Use 'dto status {run_id}' to check progress")
                
    except Exception as e:
        console.print(f"❌ Run failed: {e}", style="red")
        sys.exit(1)


def _follow_run_progress(client: httpx.Client, run_id: str):
    """Follow run progress with polling."""
    import time
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running tests...", total=None)
        
        while True:
            try:
                response = client.get(f"{global_options.api_url}/runs/{run_id}")
                if response.status_code == 200:
                    run_data = response.json()
                    status = run_data['status']
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        progress.remove_task(task)
                        
                        if status == 'completed':
                            console.print(f"✅ Run completed", style="green")
                            console.print(f"   Passed: {run_data['passed_tests']}")
                            console.print(f"   Failed: {run_data['failed_tests']}")
                            console.print(f"   Errors: {run_data['error_tests']}")
                        else:
                            console.print(f"❌ Run {status}", style="red")
                        
                        break
                    
                    time.sleep(2)  # Poll every 2 seconds
                else:
                    progress.remove_task(task)
                    console.print(f"❌ Failed to get run status: {response.status_code}", style="red")
                    break
                    
            except KeyboardInterrupt:
                progress.remove_task(task)
                console.print("\n⏹️  Stopped following (run continues in background)")
                break
            except Exception as e:
                progress.remove_task(task)
                console.print(f"❌ Error following run: {e}", style="red")
                break


@app.command()
def status(run_id: str = typer.Argument(..., help="Run ID")):
    """Get run status and results."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{global_options.api_url}/runs/{run_id}")
            
            if response.status_code == 200:
                run_data = response.json()
                
                # Display run summary
                table = Table(title=f"Run Status: {run_id}")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Suite", run_data['suite_name'])
                table.add_row("Status", run_data['status'])
                table.add_row("Started", run_data['started_at'])
                if run_data.get('ended_at'):
                    table.add_row("Ended", run_data['ended_at'])
                table.add_row("Total Tests", str(run_data['total_tests']))
                table.add_row("Passed", str(run_data['passed_tests']))
                table.add_row("Failed", str(run_data['failed_tests']))
                table.add_row("Errors", str(run_data['error_tests']))
                
                console.print(table)
                
                # Show artifacts if available
                if run_data.get('artifacts'):
                    console.print("\n📁 Artifacts:", style="bold")
                    for name, uri in run_data['artifacts'].items():
                        console.print(f"   {name}: {uri}")
                        
            else:
                console.print(f"❌ Run not found: {response.status_code}", style="red")
                sys.exit(1)
                
    except Exception as e:
        console.print(f"❌ Failed to get run status: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    app()
