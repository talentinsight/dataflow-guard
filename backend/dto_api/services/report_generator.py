"""
HTML Report Generator for ETL Test Results
"""
from datetime import datetime
from typing import Dict, Any
import json

class HTMLReportGenerator:
    """Generate beautiful HTML reports for ETL test results."""
    
    def generate_html_report(self, test_report: Dict[str, Any]) -> str:
        """Generate a comprehensive HTML report."""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Pipeline Test Report - {test_report['run_id']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333; background: #f8fafc;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1rem; opacity: 0.9; }}
        
        .summary-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }}
        .summary-card {{ 
            background: white; padding: 25px; border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-left: 4px solid #667eea;
        }}
        .summary-card h3 {{ color: #4a5568; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 0.5px; margin-bottom: 8px; }}
        .summary-card .value {{ font-size: 2rem; font-weight: bold; color: #2d3748; }}
        .summary-card .subtitle {{ color: #718096; font-size: 0.9rem; margin-top: 5px; }}
        
        .status-pass {{ border-left-color: #48bb78; }}
        .status-fail {{ border-left-color: #f56565; }}
        .status-warning {{ border-left-color: #ed8936; }}
        
        .test-results {{ background: white; border-radius: 12px; padding: 30px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 30px; }}
        .test-results h2 {{ color: #2d3748; margin-bottom: 25px; font-size: 1.5rem; }}
        
        .test-item {{ 
            border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px;
            overflow: hidden; transition: all 0.3s ease;
        }}
        .test-item:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        
        .test-header {{ 
            padding: 20px; background: #f7fafc; border-bottom: 1px solid #e2e8f0;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .test-title {{ font-weight: 600; color: #2d3748; }}
        .test-status {{ 
            padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; 
            font-weight: 600; text-transform: uppercase;
        }}
        .status-pass-badge {{ background: #c6f6d5; color: #22543d; }}
        .status-fail-badge {{ background: #fed7d7; color: #742a2a; }}
        .status-warning-badge {{ background: #feebc8; color: #7b341e; }}
        
        .test-content {{ padding: 20px; }}
        .metrics-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin-bottom: 20px;
        }}
        .metric {{ text-align: center; padding: 15px; background: #f7fafc; border-radius: 8px; }}
        .metric-value {{ font-size: 1.5rem; font-weight: bold; color: #2d3748; }}
        .metric-label {{ color: #718096; font-size: 0.9rem; margin-top: 5px; }}
        
        .issues {{ margin-top: 15px; }}
        .issue {{ 
            background: #fff5f5; border: 1px solid #fed7d7; border-radius: 6px;
            padding: 12px; margin-bottom: 8px; color: #742a2a;
        }}
        
        .recommendations {{ 
            background: white; border-radius: 12px; padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 30px;
        }}
        .recommendations h2 {{ color: #2d3748; margin-bottom: 20px; }}
        .recommendation {{ 
            background: #f0fff4; border: 1px solid #9ae6b4; border-radius: 8px;
            padding: 15px; margin-bottom: 12px; color: #22543d;
        }}
        
        .raw-data {{ 
            background: #1a202c; color: #e2e8f0; padding: 20px; border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace; font-size: 0.9rem;
            overflow-x: auto; margin-top: 15px;
        }}
        
        .footer {{ 
            text-align: center; padding: 30px; color: #718096; font-size: 0.9rem;
            border-top: 1px solid #e2e8f0; margin-top: 40px;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 2rem; }}
            .summary-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 ETL Pipeline Test Report</h1>
            <p>Run ID: {test_report['run_id']} | Generated: {test_report.get('report_generated_at', 'N/A')}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card status-{test_report['executive_summary']['overall_status'].lower()}">
                <h3>Overall Status</h3>
                <div class="value">{test_report['executive_summary']['overall_status']}</div>
                <div class="subtitle">Pipeline Health</div>
            </div>
            
            <div class="summary-card">
                <h3>Data Quality Score</h3>
                <div class="value">{test_report['executive_summary']['data_quality_score']}%</div>
                <div class="subtitle">Overall Quality</div>
            </div>
            
            <div class="summary-card">
                <h3>Tests Executed</h3>
                <div class="value">{test_report['executive_summary']['total_tests']}</div>
                <div class="subtitle">{test_report['executive_summary']['tests_passed']} passed, {test_report['executive_summary']['tests_failed']} failed</div>
            </div>
            
            <div class="summary-card">
                <h3>Execution Time</h3>
                <div class="value">{test_report['executive_summary']['execution_time_seconds']:.1f}s</div>
                <div class="subtitle">Test Duration</div>
            </div>
        </div>
        
        <div class="test-results">
            <h2>📊 Detailed Test Results</h2>
            {self._generate_test_results_html(test_report['detailed_results'])}
        </div>
        
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            {self._generate_recommendations_html(test_report['recommendations'])}
        </div>
        
        <div class="footer">
            <p>Generated by DataFlowGuard ETL Testing Framework</p>
            <p>Pipeline: {test_report['test_metadata']['source_table']} → {test_report['test_metadata']['prep_table']} → {test_report['test_metadata']['mart_table']}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_test_results_html(self, test_results) -> str:
        """Generate HTML for test results section."""
        html = ""
        
        for test in test_results:
            status_class = f"status-{test['status']}-badge"
            
            # Generate metrics HTML
            metrics_html = ""
            if test.get('metrics'):
                metrics_html = '<div class="metrics-grid">'
                for key, value in test['metrics'].items():
                    label = key.replace('_', ' ').title()
                    metrics_html += f'''
                    <div class="metric">
                        <div class="metric-value">{value}</div>
                        <div class="metric-label">{label}</div>
                    </div>'''
                metrics_html += '</div>'
            
            # Generate issues HTML
            issues_html = ""
            if test.get('issues'):
                issues_html = '<div class="issues">'
                for issue in test['issues']:
                    issues_html += f'<div class="issue">⚠️ {issue}</div>'
                issues_html += '</div>'
            
            # Generate raw data HTML
            raw_data_html = ""
            if test.get('raw_data'):
                raw_data_json = json.dumps(test['raw_data'], indent=2)
                raw_data_html = f'<div class="raw-data">{raw_data_json}</div>'
            
            html += f'''
            <div class="test-item">
                <div class="test-header">
                    <div class="test-title">{test['test_name']}</div>
                    <div class="test-status {status_class}">{test['status']}</div>
                </div>
                <div class="test-content">
                    {metrics_html}
                    {issues_html}
                    {raw_data_html}
                </div>
            </div>'''
        
        return html
    
    def _generate_recommendations_html(self, recommendations) -> str:
        """Generate HTML for recommendations section."""
        if not recommendations:
            return '<div class="recommendation">✅ No issues found - pipeline is healthy!</div>'
        
        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        
        return html
