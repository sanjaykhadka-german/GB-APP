// Initialize editable cells function
function initializeEditableCells() {
    // Handle double-click to edit
    document.querySelectorAll('.editable-cell').forEach(cell => {
        cell.addEventListener('dblclick', function() {
            if (!this.classList.contains('editing')) {
                const currentValue = this.textContent.trim();
                const input = document.createElement('input');
                input.type = 'number';
                input.step = '0.01';
                input.value = currentValue;
                input.classList.add('form-control');
                
                // Store original content
                this.dataset.originalContent = this.innerHTML;
                this.innerHTML = '';
                this.appendChild(input);
                this.classList.add('editing');
                
                input.focus();
                input.select();
                
                // Handle input blur
                input.addEventListener('blur', function() {
                    handleCellUpdate(cell);
                });
                
                // Handle enter key
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        handleCellUpdate(cell);
                    }
                });

                // Handle escape key
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        cell.innerHTML = cell.dataset.originalContent;
                        cell.classList.remove('editing');
                    }
                });
            }
        });
    });
}

// Handle cell update
function handleCellUpdate(cell) {
    if (!cell.classList.contains('editing')) return;
    
    const input = cell.querySelector('input');
    if (!input) return;

    const newValue = parseFloat(input.value) || 0;
    const id = cell.dataset.id;
    const field = cell.dataset.field;

    // Validate input
    if (isNaN(newValue) || newValue < 0) {
        alert('Please enter a valid positive number');
        cell.innerHTML = cell.dataset.originalContent;
        cell.classList.remove('editing');
        return;
    }
    
    // Send update to server - use the correct route
    fetch('/update_daily_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: id,
            field: field,
            value: newValue
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update the cell value
            cell.innerHTML = newValue.toFixed(2);
            cell.classList.remove('editing');
            
            // Update total planned
            const row = cell.closest('tr');
            if (row) {
                const totalPlannedCell = row.querySelector('.total-planned');
                if (totalPlannedCell) {
                    totalPlannedCell.textContent = data.total_planned.toFixed(2);
                }
                
                // Update variance
                const varianceCell = row.querySelector('.variance');
                if (varianceCell) {
                    varianceCell.textContent = data.variance.toFixed(2);
                }
            }
            
            // Add visual feedback
            cell.classList.add('updated');
            setTimeout(() => cell.classList.remove('updated'), 1000);
        } else {
            // Revert changes on error
            cell.innerHTML = cell.dataset.originalContent;
            cell.classList.remove('editing');
            alert('Error updating value: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        cell.innerHTML = cell.dataset.originalContent;
        cell.classList.remove('editing');
        alert('Error updating value. Please try again.');
    });
}

// Add styles for visual feedback
const style = document.createElement('style');
style.textContent = `
    .editable-cell.updated {
        animation: flash-update 1s;
    }
    
    @keyframes flash-update {
        0% { background-color: #28a745; }
        100% { background-color: #f8f9fa; }
    }
`;
document.head.appendChild(style); 