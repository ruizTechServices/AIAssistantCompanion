// Worksheet Generator JavaScript

let currentJobId = null;
let pollingInterval = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadMyWorksheets();
});

function setupEventListeners() {
    // Form submission
    const form = document.getElementById('worksheetForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Interactive view button
    const viewInteractiveBtn = document.getElementById('viewInteractiveBtn');
    viewInteractiveBtn.addEventListener('click', toggleInteractivePreview);
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = {
        gradeLevel: document.getElementById('gradeLevel').value,
        topic: document.getElementById('topic').value,
        activities: document.getElementById('activities').value,
        style: document.getElementById('style').value,
        imagesAllowed: document.getElementById('imagesAllowed').checked
    };
    
    // Validate form
    if (!formData.gradeLevel || !formData.topic || !formData.activities || !formData.style) {
        showAlert('Please fill in all required fields.', 'warning');
        return;
    }
    
    try {
        showGenerationStatus();
        
        const response = await fetch('/api/worksheet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create worksheet');
        }
        
        const result = await response.json();
        currentJobId = result.job_id;
        
        startPolling();
        
    } catch (error) {
        console.error('Error creating worksheet:', error);
        showAlert(`Error: ${error.message}`, 'danger');
        hideGenerationStatus();
    }
}

function showGenerationStatus() {
    document.getElementById('statusSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Scroll to status section
    document.getElementById('statusSection').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
    });
}

function hideGenerationStatus() {
    document.getElementById('statusSection').style.display = 'none';
}

function startPolling() {
    if (!currentJobId) return;
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/worksheet/${currentJobId}/status`);
            
            if (!response.ok) {
                throw new Error('Failed to get status');
            }
            
            const status = await response.json();
            updateStatusDisplay(status);
            
            if (status.status === 'done') {
                stopPolling();
                showResults(status);
                loadMyWorksheets(); // Refresh the list
            } else if (status.status === 'error') {
                stopPolling();
                showError(status.error_message);
            }
            
        } catch (error) {
            console.error('Error polling status:', error);
            stopPolling();
            showAlert('Error checking status. Please refresh the page.', 'danger');
        }
    }, 2000); // Poll every 2 seconds
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function updateStatusDisplay(status) {
    const statusText = document.getElementById('statusText');
    const statusDescription = document.getElementById('statusDescription');
    const progressBar = document.querySelector('.progress-bar');
    
    switch (status.status) {
        case 'pending':
            statusText.textContent = 'Queued for processing...';
            statusDescription.textContent = 'Your worksheet is in the queue and will start processing shortly.';
            progressBar.style.width = '10%';
            break;
        case 'in_progress':
            statusText.textContent = 'AI is generating your worksheet...';
            statusDescription.textContent = 'Creating content structure, generating text, and assembling your worksheet. This may take 1-2 minutes.';
            progressBar.style.width = '60%';
            progressBar.classList.add('progress-bar-animated');
            break;
    }
}

function showResults(status) {
    hideGenerationStatus();
    
    const resultsSection = document.getElementById('resultsSection');
    const downloadBtn = document.getElementById('downloadPdfBtn');
    
    downloadBtn.href = `/${status.pdf_path}`;
    
    // Store interactive path for later use
    downloadBtn.dataset.interactivePath = status.interactive_path;
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
    });
    
    showAlert('Worksheet generated successfully!', 'success');
}

function showError(errorMessage) {
    hideGenerationStatus();
    showAlert(`Generation failed: ${errorMessage}`, 'danger');
}

function toggleInteractivePreview() {
    const preview = document.getElementById('interactivePreview');
    const frame = document.getElementById('interactiveFrame');
    const downloadBtn = document.getElementById('downloadPdfBtn');
    const interactivePath = downloadBtn.dataset.interactivePath;
    
    if (preview.style.display === 'none') {
        frame.src = `/${interactivePath}`;
        preview.style.display = 'block';
        document.getElementById('viewInteractiveBtn').innerHTML = 
            '<i class="fas fa-eye-slash me-2"></i>Hide Interactive';
    } else {
        preview.style.display = 'none';
        frame.src = '';
        document.getElementById('viewInteractiveBtn').innerHTML = 
            '<i class="fas fa-desktop me-2"></i>View Interactive';
    }
}

async function loadMyWorksheets() {
    const container = document.getElementById('worksheetsList');
    
    try {
        const response = await fetch('/api/worksheets');
        
        if (!response.ok) {
            throw new Error('Failed to load worksheets');
        }
        
        const worksheets = await response.json();
        
        if (worksheets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <h5>No Worksheets Yet</h5>
                    <p>Generate your first worksheet using the form above!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = worksheets.map(ws => createWorksheetItem(ws)).join('');
        
    } catch (error) {
        console.error('Error loading worksheets:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load worksheets. Please refresh the page.
            </div>
        `;
    }
}

function createWorksheetItem(worksheet) {
    const createdDate = new Date(worksheet.created_at).toLocaleDateString();
    const statusClass = `status-${worksheet.status}`;
    const statusText = worksheet.status.charAt(0).toUpperCase() + worksheet.status.slice(1);
    
    let actions = '';
    if (worksheet.status === 'done') {
        actions = `
            <div class="btn-group" role="group">
                <a href="/${worksheet.pdf_path}" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-download me-1"></i> PDF
                </a>
                <button class="btn btn-sm btn-outline-secondary" onclick="openInteractive('${worksheet.interactive_path}')">
                    <i class="fas fa-external-link-alt me-1"></i> Interactive
                </button>
            </div>
        `;
    } else if (worksheet.status === 'error') {
        actions = `<span class="text-danger"><i class="fas fa-times me-1"></i> Failed</span>`;
    } else {
        actions = `<span class="text-warning"><i class="fas fa-clock me-1"></i> Processing</span>`;
    }
    
    return `
        <div class="worksheet-item border-bottom py-3">
            <div class="row align-items-center">
                <div class="col-md-6">
                    <div class="d-flex align-items-center">
                        <span class="status-indicator ${statusClass}"></span>
                        <div>
                            <h6 class="mb-1">${escapeHtml(worksheet.topic)}</h6>
                            <small class="text-muted">
                                Grade ${worksheet.grade_level} • ${createdDate} • ${statusText}
                            </small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 text-md-end mt-2 mt-md-0">
                    ${actions}
                </div>
            </div>
        </div>
    `;
}

function openInteractive(interactivePath) {
    window.open(`/${interactivePath}`, '_blank');
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-notification');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show alert-notification position-fixed" 
             style="top: 20px; right: 20px; z-index: 1050; max-width: 400px;">
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert-notification');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle page visibility changes to pause/resume polling
document.addEventListener('visibilitychange', function() {
    if (document.hidden && pollingInterval) {
        stopPolling();
    } else if (!document.hidden && currentJobId) {
        startPolling();
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    stopPolling();
});
