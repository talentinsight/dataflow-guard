import { useState } from 'react'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [showNewTestModal, setShowNewTestModal] = useState(false)
  const [showDataSourceModal, setShowDataSourceModal] = useState(false)

  const renderNavigation = () => (
    <nav className="navbar">
      <div className="nav-brand">
        <h1>DataFlowGuard</h1>
        <span className="nav-subtitle">Data Quality Platform</span>
      </div>
      <div className="nav-links">
        <button 
          className={currentPage === 'dashboard' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentPage('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={currentPage === 'tests' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentPage('tests')}
        >
          🧪 Test Builder
        </button>
        <button 
          className={currentPage === 'data' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentPage('data')}
        >
          💾 Data Sources
        </button>
        <button 
          className={currentPage === 'runs' ? 'nav-link active' : 'nav-link'}
          onClick={() => setCurrentPage('runs')}
        >
          🚀 Runs
        </button>
      </div>
    </nav>
  )

  const renderDashboard = () => (
    <div className="page">
      <div className="page-header">
        <h2>Dashboard</h2>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={() => setShowNewTestModal(true)}>
            + New Test Suite
          </button>
          <button className="btn btn-secondary" onClick={() => setShowDataSourceModal(true)}>
            + Add Data Source
          </button>
        </div>
      </div>
      
      <div className="grid grid-3">
        <div className="stat-card">
          <h3>Total Tests</h3>
          <div className="stat-number">2,847</div>
          <div className="stat-change">+12% this month</div>
        </div>
        
        <div className="stat-card">
          <h3>Success Rate</h3>
          <div className="stat-number">96.8%</div>
          <div className="stat-change">+2.1% improvement</div>
        </div>
        
        <div className="stat-card">
          <h3>Active Runs</h3>
          <div className="stat-number">7</div>
          <div className="stat-change">Currently running</div>
        </div>
      </div>
      
      <div className="card">
        <div className="card-header">
          <h3>Recent Runs</h3>
          <button className="btn btn-link" onClick={() => setCurrentPage('runs')}>View All →</button>
        </div>
        <div className="runs-list">
          <div className="run-item clickable" onClick={() => alert('Run Details: Customer Data Validation')}>
            <div className="run-info">
              <span className="run-name">Customer Data Validation</span>
              <span className="run-time">2 minutes ago</span>
            </div>
            <span className="status-success">✓ Success</span>
          </div>
          <div className="run-item clickable" onClick={() => alert('Run Details: Order Processing Check')}>
            <div className="run-info">
              <span className="run-name">Order Processing Check</span>
              <span className="run-time">8 minutes ago</span>
            </div>
            <span className="status-success">✓ Success</span>
          </div>
          <div className="run-item clickable" onClick={() => alert('Run Details: Payment Gateway Tests')}>
            <div className="run-info">
              <span className="run-name">Payment Gateway Tests</span>
              <span className="run-time">15 minutes ago</span>
            </div>
            <span className="status-failed">✗ Failed</span>
          </div>
        </div>
      </div>
    </div>
  )

  const renderTestBuilder = () => (
    <div className="page">
      <div className="page-header">
        <h2>Test Builder</h2>
        <button className="btn btn-primary" onClick={() => alert('Creating new test...')}>
          + Create Test
        </button>
      </div>
      
      <div className="grid grid-2">
        <div className="card">
          <h3>Quick Templates</h3>
          <div className="template-list">
            <button className="template-item" onClick={() => alert('Creating Data Quality test...')}>
              <div className="template-icon">🔍</div>
              <div>
                <div className="template-name">Data Quality Check</div>
                <div className="template-desc">Validate data completeness and accuracy</div>
              </div>
            </button>
            <button className="template-item" onClick={() => alert('Creating Schema test...')}>
              <div className="template-icon">📋</div>
              <div>
                <div className="template-name">Schema Validation</div>
                <div className="template-desc">Check column types and constraints</div>
              </div>
            </button>
            <button className="template-item" onClick={() => alert('Creating Freshness test...')}>
              <div className="template-icon">⏰</div>
              <div>
                <div className="template-name">Data Freshness</div>
                <div className="template-desc">Monitor data update frequency</div>
              </div>
            </button>
          </div>
        </div>
        
        <div className="card">
          <h3>Recent Test Suites</h3>
          <div className="test-list">
            <div className="test-item">
              <span>Customer Data Validation</span>
              <button className="btn btn-small" onClick={() => alert('Editing test suite...')}>Edit</button>
            </div>
            <div className="test-item">
              <span>Order Processing Check</span>
              <button className="btn btn-small" onClick={() => alert('Editing test suite...')}>Edit</button>
            </div>
            <div className="test-item">
              <span>Payment Gateway Tests</span>
              <button className="btn btn-small" onClick={() => alert('Editing test suite...')}>Edit</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderDataSources = () => (
    <div className="page">
      <div className="page-header">
        <h2>Data Sources</h2>
        <button className="btn btn-primary" onClick={() => setShowDataSourceModal(true)}>
          + Add Connection
        </button>
      </div>
      
      <div className="card">
        <h3>Connected Sources</h3>
        <div className="datasource-list">
          <div className="datasource-item">
            <div className="datasource-info">
              <div className="datasource-icon">❄️</div>
              <div>
                <div className="datasource-name">Snowflake Production</div>
                <div className="datasource-desc">PROD.ANALYTICS • 47 tables</div>
              </div>
            </div>
            <div className="datasource-status">
              <span className="status-success">● Connected</span>
              <button className="btn btn-small" onClick={() => alert('Testing Snowflake connection...')}>Test</button>
            </div>
          </div>
          <div className="datasource-item">
            <div className="datasource-info">
              <div className="datasource-icon">🐘</div>
              <div>
                <div className="datasource-name">PostgreSQL Staging</div>
                <div className="datasource-desc">staging.company.com • 23 tables</div>
              </div>
            </div>
            <div className="datasource-status">
              <span className="status-success">● Connected</span>
              <button className="btn btn-small" onClick={() => alert('Testing PostgreSQL connection...')}>Test</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderRuns = () => (
    <div className="page">
      <div className="page-header">
        <h2>Test Runs</h2>
        <button className="btn btn-primary" onClick={() => alert('Running all tests...')}>
          ▶ Run All Tests
        </button>
      </div>
      
      <div className="card">
        <div className="runs-filter">
          <select className="filter-select">
            <option>All Statuses</option>
            <option>Success</option>
            <option>Failed</option>
            <option>Running</option>
          </select>
          <input type="text" placeholder="Search runs..." className="filter-input" />
        </div>
        
        <div className="runs-table">
          <div className="table-header">
            <div>Test Suite</div>
            <div>Status</div>
            <div>Started</div>
            <div>Duration</div>
            <div>Actions</div>
          </div>
          <div className="table-row">
            <div>Customer Data Validation</div>
            <div><span className="status-success">✓ Success</span></div>
            <div>2 min ago</div>
            <div>45s</div>
            <div>
              <button className="btn btn-small" onClick={() => alert('Viewing run details...')}>View</button>
              <button className="btn btn-small" onClick={() => alert('Re-running test...')}>Re-run</button>
            </div>
          </div>
          <div className="table-row">
            <div>Payment Gateway Tests</div>
            <div><span className="status-failed">✗ Failed</span></div>
            <div>15 min ago</div>
            <div>32s</div>
            <div>
              <button className="btn btn-small" onClick={() => alert('Viewing failure details...')}>Debug</button>
              <button className="btn btn-small" onClick={() => alert('Re-running test...')}>Re-run</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderModal = (title: string, content: React.ReactNode, onClose: () => void) => (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-content">
          {content}
        </div>
      </div>
    </div>
  )

  return (
    <div className="app">
      {renderNavigation()}
      
      <main className="main-content">
        {currentPage === 'dashboard' && renderDashboard()}
        {currentPage === 'tests' && renderTestBuilder()}
        {currentPage === 'data' && renderDataSources()}
        {currentPage === 'runs' && renderRuns()}
      </main>

      {showNewTestModal && renderModal(
        'Create New Test Suite',
        <div>
          <div className="form-group">
            <label>Suite Name</label>
            <input type="text" placeholder="e.g., Customer Data Validation" className="form-input" />
          </div>
          <div className="form-group">
            <label>Data Source</label>
            <select className="form-select">
              <option>Snowflake Production</option>
              <option>PostgreSQL Staging</option>
            </select>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={() => {
              alert('Test suite created!')
              setShowNewTestModal(false)
            }}>Create Suite</button>
            <button className="btn btn-secondary" onClick={() => setShowNewTestModal(false)}>Cancel</button>
          </div>
        </div>,
        () => setShowNewTestModal(false)
      )}

      {showDataSourceModal && renderModal(
        'Add Data Source',
        <div>
          <div className="form-group">
            <label>Connection Type</label>
            <select className="form-select">
              <option>Snowflake</option>
              <option>PostgreSQL</option>
              <option>MySQL</option>
              <option>BigQuery</option>
            </select>
          </div>
          <div className="form-group">
            <label>Connection Name</label>
            <input type="text" placeholder="e.g., Production Warehouse" className="form-input" />
          </div>
          <div className="form-group">
            <label>Host</label>
            <input type="text" placeholder="your-account.snowflakecomputing.com" className="form-input" />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={() => {
              alert('Testing connection...')
              setTimeout(() => {
                alert('Connection successful!')
                setShowDataSourceModal(false)
              }, 1000)
            }}>Test & Save</button>
            <button className="btn btn-secondary" onClick={() => setShowDataSourceModal(false)}>Cancel</button>
          </div>
        </div>,
        () => setShowDataSourceModal(false)
      )}
    </div>
  )
}

export default App