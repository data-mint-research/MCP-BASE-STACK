// Quality Metrics Dashboard JavaScript

// Global variables
let trendsChart = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadDashboardData();
    
    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', function() {
        runQualityChecks();
    });
});

// Load all dashboard data
function loadDashboardData() {
    // Load metrics
    fetch('/api/metrics')
        .then(response => response.json())
        .then(data => {
            updateSummaryMetrics(data);
            updateLastUpdated(data.timestamp);
        })
        .catch(error => console.error('Error loading metrics:', error));
    
    // Load trend data
    fetch('/api/trends')
        .then(response => response.json())
        .then(data => {
            updateTrendChart(data);
        })
        .catch(error => console.error('Error loading trends:', error));
    
    // Load component metrics
    fetch('/api/components')
        .then(response => response.json())
        .then(data => {
            updateComponentMetrics(data);
        })
        .catch(error => console.error('Error loading component metrics:', error));
    
    // Load improvement data
    fetch('/api/improvements')
        .then(response => response.json())
        .then(data => {
            updateImprovementTracking(data);
        })
        .catch(error => console.error('Error loading improvement data:', error));
}

// Update summary metrics
function updateSummaryMetrics(data) {
    // Documentation coverage
    const docCoverage = data.knowledge_graph?.components?.core?.documentation_coverage || 0;
    document.getElementById('documentation-coverage').textContent = formatPercentage(docCoverage);
    
    // Type hint coverage
    const typeHintCoverage = data.knowledge_graph?.components?.core?.type_hint_coverage || 0;
    document.getElementById('type-hint-coverage').textContent = formatPercentage(typeHintCoverage);
    
    // File structure compliance
    const fileStructureCompliance = data.file_structure?.overall_compliance || 0;
    document.getElementById('file-structure-compliance').textContent = formatPercentage(fileStructureCompliance / 100);
    
    // Quality issues
    const qualityIssues = data.code_quality?.total_checks || 0;
    document.getElementById('quality-issues').textContent = qualityIssues;
}

// Update last updated timestamp
function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    document.getElementById('last-updated').textContent = date.toLocaleString();
}

// Update trend chart
function updateTrendChart(data) {
    const ctx = document.getElementById('trends-chart').getContext('2d');
    
    // Format dates for display
    const labels = data.timestamps.map(ts => {
        const date = new Date(ts);
        return date.toLocaleDateString();
    });
    
    // Destroy existing chart if it exists
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    // Create new chart
    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Quality Issues',
                    data: data.code_quality?.issues_count || [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'File Structure Compliance',
                    data: data.file_structure?.overall_compliance || [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Quality Metrics Trends'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Update component metrics
function updateComponentMetrics(data) {
    const componentGrid = document.getElementById('component-grid');
    componentGrid.innerHTML = '';
    
    // Create a card for each component
    for (const [componentName, metrics] of Object.entries(data)) {
        const card = document.createElement('div');
        card.className = 'component-card';
        
        // Create card content
        card.innerHTML = `
            <h3>${componentName}</h3>
            <div class="component-metrics">
                <div class="component-metric">
                    <div class="component-metric-label">Documentation Coverage</div>
                    <div class="component-metric-value">${formatPercentage(metrics.documentation_coverage || 0)}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Type Hint Coverage</div>
                    <div class="component-metric-value">${formatPercentage(metrics.type_hint_coverage || 0)}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Issues</div>
                    <div class="component-metric-value">${metrics.issues_count || 0}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Complexity</div>
                    <div class="component-metric-value">${metrics.complexity_cyclomatic || 0}</div>
                </div>
            </div>
        `;
        
        // Add card to grid
        componentGrid.appendChild(card);
    }
    
    // If no components, show a message
    if (Object.keys(data).length === 0) {
        componentGrid.innerHTML = '<p>No component metrics available.</p>';
    }
}

// Update improvement tracking
function updateImprovementTracking(data) {
    const tableBody = document.getElementById('improvement-table-body');
    tableBody.innerHTML = '';
    
    // Create a row for each metric
    for (let i = 0; i < data.metrics.length; i++) {
        const row = document.createElement('tr');
        
        // Calculate change class
        const changeValue = data.change[i];
        const changeClass = changeValue > 0 ? 'positive-change' : (changeValue < 0 ? 'negative-change' : '');
        
        // Create row content
        row.innerHTML = `
            <td>${data.metrics[i]}</td>
            <td>${formatValue(data.targets[i])}</td>
            <td>${formatValue(data.current[i])}</td>
            <td>${formatValue(data.previous[i])}</td>
            <td class="${changeClass}">${formatChange(changeValue)}</td>
        `;
        
        // Add row to table
        tableBody.appendChild(row);
    }
    
    // If no metrics, show a message
    if (data.metrics.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No improvement data available.</td></tr>';
    }
}

// Run quality checks
function runQualityChecks() {
    // Show loading state
    document.getElementById('refresh-btn').textContent = 'Running...';
    document.getElementById('refresh-btn').disabled = true;
    
    // Run checks
    fetch('/api/run-checks', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Reload dashboard data
                loadDashboardData();
                alert('Quality checks completed successfully.');
            } else {
                alert(`Error running quality checks: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error running quality checks:', error);
            alert('Error running quality checks. See console for details.');
        })
        .finally(() => {
            // Reset button
            document.getElementById('refresh-btn').textContent = 'Refresh Metrics';
            document.getElementById('refresh-btn').disabled = false;
        });
}

// Format percentage value
function formatPercentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

// Format change value
function formatChange(value) {
    if (value === 0) return '0';
    return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
}

// Format value based on type
function formatValue(value) {
    if (typeof value === 'number') {
        // If it's a percentage (between 0 and 1)
        if (value >= 0 && value <= 1) {
            return formatPercentage(value);
        }
        // If it's a percentage (between 0 and 100)
        else if (value >= 0 && value <= 100 && value.toString().includes('.')) {
            return `${value.toFixed(1)}%`;
        }
        // Otherwise, just format the number
        return value.toFixed(0);
    }
    return value;
}