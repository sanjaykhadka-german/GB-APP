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
}); 