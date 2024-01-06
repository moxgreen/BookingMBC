
$(document).ready(function() {
//document.addEventListener('DOMContentLoaded', function () {
    var formattedBookingsData = $('#formatted-bookings-data').data('json');
    var uname = $('#username').data('username');
    var fname = $('#facility').data('facility');
    var gname = $('#groupname').data('groupname');
    var cmach = $('#currmachine').data('currmachine');
    var maxbt = $('#timelimit').data('timelimit');
    var selected;

    // Using delegation for the 'shown.bs.modal' event
    $(document).on('shown.bs.modal', '#bookingFormModal', function () {
        // Focus on the text input when the modal is shown
        $('#titleInput').focus();
    });

    var calendarMonth = new FullCalendar.Calendar( document.getElementById('calendar-month'), {
        // Configure the month calendar
        initialView: 'dayGridMonth',
        // Add event sources and other configuration as needed
        initialDate: new Date(),
        headerToolbar: {
          left: 'prev,today,next',
          center: 'title',
          right: ''
        },
    
    });
    
    var calendarWeek = new FullCalendar.Calendar( document.getElementById('calendar-week'), {
        // Configure the week calendar
        initialView: 'timeGridWeek',
        // Add other configurations
        initialDate: new Date(),
        editable: true,
        selectable: true,
        unselectAuto: false,
        selectMirror: true,
        eventOverlap: false,
        selectOverlap: false,
        allDaySlot: false,
        dayMaxEvents: true, // allow "more" link when too many events
        events: formattedBookingsData,
        
        headerToolbar: {
          left: '',
          center: 'title',
          right: 'prev,today,next timeGridWeek,timeGridDay'
        },

        // constrain to a discrete range: from today to 3 months later
        validRange: get3MonthsRange(new Date()), // Pass the current date to the function
       
        // a new booking is requested
        select: function(info) {
            // Prepare to show the modal form asking for more details
            selected=info; // use global variable for future access to this data
            let nowDate = new Date();
            // Check if the event's start time is in the past
            if (info.start < nowDate) {
                calendarWeek.unselect();
                return false;
            }
            // Check if the time selected is larger than maxTime for this machine
            if ( !isWithinTimeLimits(info.start, info.end) ) {
                alert('This service cannot be booked for longer than ' + maxbt + " minutes");
                calendarWeek.unselect();
                return false;            
            }
            //ok now finally show the modal form
            $('#bookingFormModal').modal('show');
            
            $('#saveChangesBtn').on('click', function() {
                // Your save changes logic...
                var title = $('#titleInput').val();
                var assistance = $('input[name="assistance"]:checked').val();
                //console.log("title: " + title + " assistance: " + assistance)

                if (!title) {
                    // Handle the Cancel scenario (no text provided or modal closed without saving)
                    //console.log("NO title close modal and unselect calendar");
                    calendarWeek.unselect();
                    $('#bookingFormModal').modal('hide');
                    return;
                }
                
                // Create new event to send via ajax GET with the obtained values
                var newEvent = {
                    currentmachine: $('#currmachine').data('currmachine'),
                    title: gname + "\/" + uname + ": " + title,
                    start: selected.startStr,
                    end: selected.endStr,
                    assistance: assistance,
                };
        
                // save the event to a server or update the UI.
                $.ajax({
                    url: 'add_booking',
                    method: 'GET', //better for more complex data
                    type: 'GET',
                    data: newEvent,
                    dataType: "json",
                    success: function (data) {
                          calendarWeek.addEvent(newEvent);
                          calendarWeek.unselect();
                    },
                    error: function (data) {
                          alert('There is a problem!!!');
                    }
                }); //$.ajax

                $('#bookingFormModal').modal('hide');
            }); //('#saveChangesBtn').on('click'
            
            
            $('#bookingFormModal').on('hidden.bs.modal', function () {           
                // Clear text box and radio buttons
                $('#titleInput').val('');
                $('input[name="assistance"]').prop('checked', false);
            
                // Optionally, reset radio button to a default value (e.g., 'No Assistance Needed')
                $('#assistanceNo').prop('checked', true);
                calendarWeek.unselect();
            });
        }, //select
        

        eventChange: function(changeInfo) {
        //drag/resize an event

              var nowDate = new Date();
              // Check if the event's start time is in the past
              if (changeInfo.event.start < nowDate) {
                  // Revert the event to its original position
                  changeInfo.revert();
                  alert("You cannot drag the event to the past!");
                  return false;
              }
              // Check if the time selected is larger than maxTime for this machine
              if ( !isWithinTimeLimits(changeInfo.start, changeInfo.end) ) {
                    changeInfo.revert();
                    alert('This service cannot be booked for longer than ' + maxbt + " minutes");
                    return false;            
              }

              var newStartStr =  changeInfo.event.startStr;
              var newEndStr =  changeInfo.event.endStr;
              var oldStartStr =  changeInfo.oldEvent.startStr;
              var moveEvent = {
                  currentmachine: $('#currmachine').data('currmachine'),
                  newStart: newStartStr,
                  newEnd: newEndStr,
                  oldStart: oldStartStr,
              };
    
              // save the event to a server or update the UI.
              $.ajax({
                  url: 'move_booking',
                  method: 'GET', //better for more complex data
                  type: 'GET',
                  data: moveEvent,
                  dataType: "json",
                  success: function (data) {
                        //calendarWeek.addEvent(moveEvent);
                        calendarWeek.unselect();
                  },
                  error: function (data) {
                      alert('There is a problem in dragging a booking!!!');
                  }
              }); //$.ajax

              //alert('Old time: ' + oldDateStr + ' changed into new time:' + newDateStr);
        }, //eventChange
 
         
        //deleting a Booking                       
        eventClick: function(arg) {
             if ( arg.event.backgroundColor == 'grey') return;
             var nowDate = new Date();
             // Check if the event's start time is in the past
             if (arg.event.start < nowDate) return;
             
             if (confirm('Are you sure you want to delete this event?')) {
                var Event2Del = {
                    currentmachine: $('#currmachine').data('currmachine'),
                    title:  arg.event.title,
                    start:  arg.event.startStr,
                };            

                $.ajax({
                   url: 'del_booking',
                   method: 'GET',
                   type: 'GET',

                   data: Event2Del,
                   dataType: "json",

                   success: function(response) {
                     arg.event.remove()
                   },
                   error: function (data) {
                     alert('There is a problem!!!');
                   }
                }); //$.ajax
             } //if confirm
        }, //eventClick
               
    }); //calendarWeek

    calendarMonth.render();
    calendarWeek.render();
    

    // Store references to the calendar instances for later use
    var calendars = {
        month: calendarMonth,
        week: calendarWeek,
    };

    // Attach click event handler to the month calendar so that the calendar-month can talk to clendar-week
    calendarMonth.on( 'dateClick', function (info) {
        // Handle the date click event
        // Update the week calendar to show the selected day
        updateWeekCalendar(calendars.week, info.date);
    });
    


    /*********** machines/facility buttons ***********/
    
    // 1) Handle click event for the "previous service" button
    $('#previousServiceButton').on('click', function() {
        changemachine(calendars.week, 'previous')
    }); //on previous
    
    // 2) Handle click event for the "next service" button
    $('#nextServiceButton').on('click', function() {
        changemachine(calendars.week, 'next')
    }); // on next

    // 3) Handle click event + Event delegation for standard & dynamically added machines
    $('#machines-list').on('click', '.dropdown-item', function (event) {
        // Prevent the default link behavior of href=#
        event.preventDefault();
        // Access the clicked item's data-itemname attribute
        var clickedItemname = $(this).data('itemname');
        changemachine(calendars.week, 'select', clickedItemname);
    }); // dynamically added machines

    // 4) Handle click event for the Facilities dropdown menu
    $('#facilities-list .dropdown-item').on('click', function () {
        var selectedItem = $(this).data('facility');
        if (selectedItem == $('#facility').data('facility')) {
            return;
        }
        changefacility(calendars.week, selectedItem)
    }); //on dropdown facilities   



    /*********** machines percent of usage table ***********/
    
    // Handle click event for the calendar buttons
    $('#calendar-week .fc-next-button').on('click', function(){
        var sun = calendars.week.currentData.currentDate.toISOString();
        updateTable(sun);
    });
    
    // Handle click event for the calendar buttons
    $('#calendar-week .fc-prev-button').on('click', function(){
        var sun = calendars.week.currentData.currentDate.toISOString();
        updateTable(sun);
    });

    // Handle click event for the calendar buttons
    $('#calendar-week .fc-today-button').on('click', function(){
        var sun = calendars.week.currentData.currentDate.toISOString();
        updateTable(sun);
    });

}); //$(document)




/*********** machines/facility buttons ***********/

function changefacility(calendar, itemname) {
    // clear old bookings for the previous machine and fetch the next with its bookings
    calendar.removeAllEvents();
    fname = itemname
    $('#facility').data('facility');
    
    var sun = calendar.currentData.currentDate.toISOString();
 
    var currfac  = {
        selecteditem: itemname,
        start: sun,
    };
     
    $.ajax({
        url: 'select_facility',
        method: 'GET', //better for more complex data
        type: 'GET',
        data : currfac,
        dataType: "json",
        success: function (response) {
            var responseObject = JSON.parse(response);
            var calendarevents = JSON.parse(responseObject.formatted_bookings_json);
   
            $('#change_machine h3:first').text('Booking: ' + responseObject.machine2BookName);
            $('#currmachine').data('currmachine', responseObject.machine2BookName);
            $('#facility').data('facility', responseObject.facilityname);
            $('#timelimit').data('timelimit', responseObject.timelimit);
            $('#change_machine h3:eq(1)').text('from the ' + responseObject.facilityname + ' facility');
            
            //update the list of dropdown menus
            // Select the dropdown menu by its ID
            var dropdownMenu = $('#machines-list');
            // Remove existing items from the dropdown
            dropdownMenu.empty();
            var items = responseObject.otherMachinesInCurrentFacility;
            // Add new items to the dropdown
            for (var i = 0; i < items.length; i++) {
                var li_item = '<li><a class="dropdown-item" href="#" data-itemname="' + items[i] + '">' + items[i] + '</a></li>';
                dropdownMenu.append(li_item);
            }
            calendar.setOption('events', calendarevents);
            calendar.unselect();

            updateTableContent(responseObject.usage_dict);
        },
        error: function (response) {
            alert('Change facility button has a problem!!!');
        }
    }); //ajax
   
};


function changemachine(calendar, direction, itemname='') {
    // clear old bookings for the previous machine and fetch the next with its bookings
    calendar.removeAllEvents();
    cmach = $('#currmachine').data('currmachine');

    var currmac  = {
        currmachine:  cmach,
        selecteditem: itemname,
    };
     
    $.ajax({
        url: direction+'_machine',
        method: 'GET', //better for more complex data
        type: 'GET',
        data : currmac,
        dataType: "json",
        success: function (response) {
            var responseObject = JSON.parse(response);
            var calendarevents = JSON.parse(responseObject.formatted_bookings_json);
   
            $('#change_machine h3:first').text('Booking: ' + responseObject.machine2BookName);
            $('#currmachine').data('currmachine', responseObject.machine2BookName);
            $('#timelimit').data('timelimit', responseObject.timelimit);
            calendar.setOption('events', calendarevents);
            calendar.unselect();
        },
        error: function (response) {
              alert('change machine button has a problem!!!');
        }
    }); //ajax
};



/*********** machines % of usage HTML table ***********/

function updateTable(start) {
    //fecth updated values from server
    var usage = {
        start: start,
        facility: $('#facility').data('facility'),
    };
    
    $.ajax({
        url: 'machines_usage',
        method: 'GET',
        type: 'GET',
        data: usage,
        dataType: "json",
        success: function(data) {
            // Update the table content based on the received data
            console.log(data)
            updateTableContent(data);
        },
        error: function(error) {
            alert('Error fetching table data:' + error);
        }
    });
}; //updateTable


function updateTableContent(updatedData) {
    // Clear the entire content within #machinesTable tbody and show a new table
    $('#machinesTable tbody').empty();

    // Create the table body
    var tableBody = $('<tbody></tbody>');
    $.each(updatedData, function (machineName, dailyUsageInAWeek) {
        var newRow = $('<tr data-machine-name="' + machineName + '"></tr>');
        newRow.append('<td>' + machineName + '</td>');

        $.each(dailyUsageInAWeek, function (index, usage) {
            if (usage == 0) {
                newRow.append('<td class="table-light">Free</td>');
            } else {
                var cellClass = (usage < 30) ? 'table-success' : (usage < 60) ? 'table-warning' : 'table-danger';
                newRow.append('<td class="' + cellClass + '">' + usage.toFixed(2) + '%</td>');
            }
        });

        tableBody.append(newRow);
    });

    // Append the new table body to the existing table
    $('#machinesTable').append(tableBody);
}; //updateTableContent


/*********** calendar month-week crosstalk ***********/

//let calendarMonth talk to calendarWeekendar and update the date with that of calendarMonth
function updateWeekCalendar(calendar, selectedDate) {
    // Update the week calendar to show the selected day
    calendar.gotoDate(selectedDate);
};    

function get3MonthsRange(nowDate) {
    // Calculate the start of the week (Sunday) for the current date
    var startDate = new Date(nowDate);
    startDate.setDate(startDate.getDate() - startDate.getDay());

    var endDate = new Date(startDate);
    endDate.setMonth(endDate.getMonth() + 3); // Add 3 months to the given date
    
    return {
      start: startDate,
      end: endDate
    };
};

function getDiffInMins(start, end) {
    let timeDifference = end - start;
    // Convert milliseconds to minutes
    return parseInt(timeDifference / (1000 * 60));
}

function isWithinTimeLimits(start,end) {
    // Check if the time selected is larger than maxTime for this machine
    maxbt = parseInt($('#timelimit').data('timelimit'));
    if (maxbt == 0) {
    // if maxbt == 0 there is no time constraint
        return true;    
    }
    let duration = getDiffInMins(start, end);
    if ( duration > maxbt) {
        //duration exceeds limits
        return false;            
    }
    // duration allowed!
    return true;
}
