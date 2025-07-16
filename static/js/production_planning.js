// Initialize editable cells function
function initializeEditableCells() {
    console.log('Initializing editable cells...');
    $('.editable-cell').off('dblclick').on('dblclick', function() {
        console.log('Cell double-clicked');
        var cell = $(this);
        if (cell.hasClass('editing')) return;
        
        cell.addClass('editing');
        var originalValue = cell.text().trim();
        var input = $('<input type="number" step="0.01">').val(originalValue);
        cell.html(input);
        input.focus();

        input.on('blur keydown', function(e) {
            if (e.type === 'blur' || e.key === 'Enter') {
                console.log('Processing cell update...');
                var newValue = input.val();
                var id = cell.data('id');
                var field = cell.data('field');
                
                console.log('Updating:', { id: id, field: field, value: newValue });
                
                // Validate input
                if (isNaN(newValue) || parseFloat(newValue) < 0) {
                    alert('Please enter a valid positive number');
                    cell.text(originalValue);
                    cell.removeClass('editing');
                    return;
                }
                
                $.ajax({
                    url: '/update_daily_plan',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ id: id, field: field, value: parseFloat(newValue) }),
                    success: function(response) {
                        console.log('Update response:', response);
                        if (response.success) {
                            // Update the cell value
                            cell.text(parseFloat(newValue).toFixed(2));
                            cell.removeClass('editing');
                            
                            // Update TOTAL PLANNED and VARIANCE in the same row
                            var row = cell.closest('tr');
                            if (response.total_planned !== undefined) {
                                row.find('.total-planned').text(parseFloat(response.total_planned).toFixed(2));
                            }
                            if (response.variance !== undefined) {
                                row.find('.variance').text(parseFloat(response.variance).toFixed(2));
                            }
                            
                            // Update footer totals
                            if (typeof updateTotals === 'function') {
                                updateTotals();
                            }
                            
                            // Add visual feedback
                            cell.addClass('updated');
                            setTimeout(() => cell.removeClass('updated'), 1000);
                        } else {
                            alert('Error updating value: ' + (response.error || 'Unknown error'));
                            cell.text(originalValue);
                            cell.removeClass('editing');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('AJAX Error:', error);
                        console.error('Status:', status);
                        console.error('Response:', xhr.responseText);
                        alert('Error updating value. Please try again.');
                        cell.text(originalValue);
                        cell.removeClass('editing');
                    }
                });
            } else if (e.key === 'Escape') {
                cell.text(originalValue);
                cell.removeClass('editing');
            }
        });
    });
    console.log('Editable cells initialized');
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
    
    .editable-cell {
        position: relative;
        cursor: pointer;
    }

    .editable-cell.editing {
        padding: 0;
    }

    .editable-cell input {
        width: 100%;
        height: 100%;
        padding: 0.5rem;
        border: none;
        outline: none;
    }

    .editable-cell::after {
        content: '✎';
        position: absolute;
        top: 50%;
        right: 5px;
        transform: translateY(-50%);
        opacity: 0;
        transition: opacity 0.2s;
    }

    .editable-cell:hover::after {
        opacity: 0.5;
    }
`;
document.head.appendChild(style); 