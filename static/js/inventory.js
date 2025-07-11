$(document).ready(function() {
    // Handle item selection
    $('#item_id').on('change', function() {
        const itemId = $(this).val();
        if (itemId) {
            $.ajax({
                url: `/inventory/api/item/${itemId}`,
                method: 'GET',
                success: function(data) {
                    // Auto-fill item data
                    $('#price_per_kg').val(data.price_per_kg || 0);
                    $('#supplier_name').val(data.supplier_name || '');
                    $('#category').val(data.category || '');
                    
                    // Get current stock from stocktake
                    $.ajax({
                        url: `/inventory/api/stocktake/${itemId}`,
                        method: 'GET',
                        success: function(stockData) {
                            $('#current_stock').val(stockData.current_stock || 0);
                            calculateDailyValues();
                        }
                    });
                    
                    // Get raw material usage
                    $.ajax({
                        url: `/inventory/api/raw_material/${itemId}`,
                        method: 'GET',
                        success: function(usageData) {
                            $('#required_total').val(usageData.total_usage || 0);
                            calculateDailyValues();
                        }
                    });
                }
            });
        }
    });

    // Handle input changes
    $('input[type="number"]').on('input', function() {
        calculateDailyValues();
    });

    function calculateDailyValues() {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        let totalRequired = 0;
        
        days.forEach(day => {
            // Get values for the day
            const required = parseFloat($(`#${day}_required_kg`).val()) || 0;
            const ordered = parseFloat($(`#${day}_to_be_ordered`).val()) || 0;
            const received = parseFloat($(`#${day}_ordered_received`).val()) || 0;
            const consumed = parseFloat($(`#${day}_consumed_kg`).val()) || 0;
            
            // Calculate opening stock
            let openingStock = 0;
            if (day === 'monday') {
                openingStock = parseFloat($('#current_stock').val()) || 0;
            } else {
                const prevDay = days[days.indexOf(day) - 1];
                openingStock = parseFloat($(`#${prevDay}_closing_stock`).val()) || 0;
            }
            
            // Calculate variance
            const variance = openingStock - required;
            
            // Calculate closing stock
            const closingStock = openingStock + received - consumed;
            
            // Update fields
            $(`#${day}_opening_stock`).val(openingStock.toFixed(2));
            $(`#${day}_variance`).val(variance.toFixed(2));
            $(`#${day}_closing_stock`).val(closingStock.toFixed(2));
            
            // Add to total required
            totalRequired += required;
        });
        
        // Update totals
        $('#required_for_plan').val(totalRequired.toFixed(2));
        
        // Calculate value required
        const pricePerKg = parseFloat($('#price_per_kg').val()) || 0;
        const valueRequired = totalRequired * pricePerKg;
        $('#value_required').val(valueRequired.toFixed(2));
        
        // Calculate variance for week
        const currentStock = parseFloat($('#current_stock').val()) || 0;
        const varianceForWeek = currentStock - totalRequired;
        $('#variance_for_week').val(varianceForWeek.toFixed(2));
        
        // Update styling
        updateVarianceStyling();
    }

    function updateVarianceStyling() {
        $('input[id$="_variance"]').each(function() {
            const value = parseFloat($(this).val()) || 0;
            $(this).removeClass('text-danger text-success');
            if (value < 0) {
                $(this).addClass('text-danger');
            } else if (value > 0) {
                $(this).addClass('text-success');
            }
        });
        
        const varianceForWeek = parseFloat($('#variance_for_week').val()) || 0;
        $('#variance_for_week')
            .removeClass('text-danger text-success')
            .addClass(varianceForWeek < 0 ? 'text-danger' : varianceForWeek > 0 ? 'text-success' : '');
    }

    // Initialize calculations
    calculateDailyValues();

    // Handle double-click on editable cells
    $('.editable-cell').dblclick(function() {
        const cell = $(this);
        const currentValue = cell.text().trim();
        const field = cell.data('field');
        const inventoryId = cell.closest('tr').data('id');
        
        // Create input field
        const input = $('<input>')
            .attr('type', 'number')
            .attr('step', '0.01')
            .val(currentValue)
            .css('width', '100%');
            
        // Replace cell content with input
        cell.html(input);
        input.focus();
        
        // Handle input blur (when focus is lost)
        input.blur(function() {
            const newValue = $(this).val();
            
            // Send update to server
            $.ajax({
                url: '/inventory/update_field',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    id: inventoryId,
                    field: field,
                    value: newValue
                }),
                success: function(response) {
                    if (response.success) {
                        // Update the edited cell
                        cell.html(parseFloat(newValue).toFixed(2));
                        
                        // Update related cells in the same row
                        const row = cell.closest('tr');
                        const day = field.split('_')[0];
                        
                        // Update calculated fields
                        row.find(`td[data-field="${day}_opening_stock"]`).text(parseFloat(response.data.opening_stock).toFixed(2));
                        row.find(`td[data-field="${day}_variance"]`).text(parseFloat(response.data.variance).toFixed(2));
                        row.find(`td[data-field="${day}_closing_stock"]`).text(parseFloat(response.data.closing_stock).toFixed(2));
                        
                        // Update totals
                        row.find('td[data-field="required_for_plan"]').text(parseFloat(response.data.required_for_plan).toFixed(2));
                        row.find('td[data-field="variance_for_week"]').text(parseFloat(response.data.variance_for_week).toFixed(2));
                        row.find('td[data-field="value_required"]').text(parseFloat(response.data.value_required).toFixed(2));
                    } else {
                        alert('Error updating value');
                        cell.html(currentValue);
                    }
                },
                error: function() {
                    alert('Error communicating with server');
                    cell.html(currentValue);
                }
            });
        });
        
        // Handle Enter key
        input.keypress(function(e) {
            if (e.which == 13) {
                input.blur();
            }
        });
    });
    
    // Handle search form submission
    $('#searchForm').submit(function(e) {
        e.preventDefault();
        const params = new URLSearchParams($(this).serialize());
        window.location.href = '/inventory/?' + params.toString();
    });
    
    // Reset search form
    window.resetSearch = function() {
        $('#search_item').val('');
        $('#search_category').val('');
        $('#search_week_commencing').val('');
        $('#searchForm').submit();
    };
}); 