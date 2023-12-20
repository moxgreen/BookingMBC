$(document).ready(function() {
   
    // Enable/disable date inputs based on the selected report type
    $('#lastThreeMonths').on('change', function() {
        $('#startDateGroup').prop('disabled', true);
        $('#endDateGroup').prop('disabled', true);
    });
    
    $('#userDefinedTime').on('change', function() {
        $('#startDateGroup').prop('disabled', false);
        $('#endDateGroup').prop('disabled', false);
    });

    $('.dropdown-item').on('click', function() {
        // Get the text of the selected item
        var selectedText = $(this).text();

        // Update the button text with the selected item
        $('.dropdown-toggle').text(selectedText);
    });

    $('#downloadReportGroup').on('click', function(e) {
        e.preventDefault();

        var reportType = $('input[name="reportType"]:checked').val();
        var startDateGroup = $('#startDateGroup').val();
        var endDateGroup = $('#endDateGroup').val();        
        var selectedGroup = $('.dropdown-toggle').text().trim();
        
        // Construct the URL based on the selected options
        var queryParams = {
            groupName: selectedGroup,
            reportType: reportType
        };
        
        if (reportType === 'userDefinedTime') {
            queryParams.startDateGroup = startDateGroup;
            queryParams.endDateGroup = endDateGroup;
        }
        
        // Serialize the data for the URL
        var url = 'download_report_group/?' + $.param(queryParams);
        // Redirect to the constructed URL
        window.location.href = url;
        
        // Wait for a few seconds before redirecting to 'reports_view'
        setTimeout(function() {
            var url = 'reports_view';
            window.location.href = url;
        }, 1000); // Adjust the delay time as needed        
    });  //downloadReportGroup


    $('#downloadReportFacilities').on('click', function(e) {
        e.preventDefault();

        var startDateFacilities = $('#startDateFacilities').val();
        var endDateFacilities = $('#endDateFacilities').val();        
        
        // Construct the URL based on the selected options
        var queryParams = {
            startDateFacilities: startDateFacilities,
            endDateFacilities: endDateFacilities
        };
                
        // Serialize the data for the URL
        var url = 'download_report_facilities/?' + $.param(queryParams);
        // Redirect to the constructed URL
        window.location.href = url;
        
        // Wait for a few seconds before redirecting to 'reports_view'
        setTimeout(function() {
            var url = 'reports_view';
            window.location.href = url;
        }, 1000); // Adjust the delay time as needed        
    });  //downloadReportFacilities

}); //$(document)

