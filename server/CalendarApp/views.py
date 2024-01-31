import json
import pandas as pd
import io

from datetime import datetime, timedelta
from .models import  Booking, Machine
from UserApp.models import UserProfile, MBCGroup
from django.shortcuts import  render, HttpResponse, redirect
from django.http import JsonResponse 
from django.utils import timezone
from django.db.models import Prefetch
from django.contrib import messages


###########################################################################################################################
#                                                                                                                         #
#                                         Generate downloadable reports on costs                                          #
#                                                                                                                         #
###########################################################################################################################
    

def download_report_facilities(request):
    # Query to get a list of all unique facilities
    facilities_list = Machine.objects.values_list('facility', flat=True).distinct()   

    start_date = request.GET.get('startDateFacilities')
    end_date = request.GET.get('endDateFacilities')
    
    #define the response
    # fname="report_facilities.xlsx"
    # response = HttpResponse(content_type='application/xlsx')
    # response['Content-Disposition'] = f'attachment; filename={fname}'
    
    final_df = pd.DataFrame(columns=['Group Name'])
    for facility in facilities_list:
        df=generate_report_dataframe_facility(facility, start_date, end_date)
        if not(df.empty):
            final_df = pd.merge(final_df, df, on='Group Name', how='outer')

    # Fill NaN values with 0
    final_df.fillna("", inplace=True)
    # Create Excel file in memory
    excel_file = io.BytesIO()

    # Use ExcelWriter to set column widths
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, sheet_name='Facilities', index=False)

        # Access the XlsxWriter worksheet object
        worksheet = writer.sheets['Facilities']

        # Iterate through each column and set the width based on the maximum length of the column data
        for i, col in enumerate(final_df.columns):
            max_len = max(final_df[col].astype(str).apply(len).max(), len(col))
            worksheet.set_column(i, i, max_len + 2)  # Add a little extra space

    excel_file.seek(0)

    # Prepare response for download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report_facilities.xlsx'
    response.write(excel_file.read())

    # with pd.ExcelWriter(response) as writer:
    #     final_df.to_excel(writer, sheet_name='Facilities Cost Summary', index=False)

    return response


def generate_report_dataframe_facility(facility, start_date, end_date):
    start=datetime.strptime(start_date, '%Y-%m-%d')
    end=datetime.strptime(end_date, '%Y-%m-%d')
    # Get Booking instances for the facility
    #print('start: ', start, 'end: ', end, facility)
    bookings = Booking.objects.filter(machine_obj__facility=facility,
                                      booked_start_date__date__gte=start.date(),
                                      booked_end_date__date__lte=end.date()
                                     )
    group_costs = {}
    
    for booking in bookings:
        usn=str(booking.username)

        # Calculate the duration by subtracting booked_end_date from booked_start_date
        duration_timedelta = booking.booked_end_date - booking.booked_start_date
        duration_hours = duration_timedelta.total_seconds() / 3600
        try:
            u = UserProfile.objects.get(user__username = usn)
            # Get the group name for the user associated with the booking
            g_name = u.group.group_name
            # Get the affiliation of the user of this booking
            external = u.is_external
            mb = u.group.machines_bought
            buyer = False
            #check if the user of this booking has ever bought machines
            if (mb.count() != 0):
                thisBookedMachine = booking.machine_obj
                #search if the machine of this booking is present
                #    in the list of machines bought by the user
                buyer = u.group.machines_bought.filter(pk=thisBookedMachine.pk).exists()
        except UserProfile.DoesNotExist:
            g_name=usn+' deleted user'
            external = buyer = False            
            
        # Calculate the total cost based on the machine type (assisted or external)
        if (booking.is_assisted):
            if buyer:
                cost_field='hourly_cost_buyer_assisted'
            elif external:
                cost_field='hourly_cost_external_assisted'
            else:
                cost_field='hourly_cost_assisted'
        else:
            if buyer:
                cost_field='hourly_cost_buyer'                    
            elif external:
                cost_field='hourly_cost_external'
            else:
                cost_field='hourly_cost'

        hourly_cost = float(getattr(booking.machine_obj, cost_field))
        
        total_cost = hourly_cost * duration_hours

        # Update the dictionary with the cost for the current group
        if g_name in group_costs:
            group_costs[g_name] += total_cost
        else:
            group_costs[g_name] = total_cost
    
    # Convert the dictionary to a Pandas DataFrame
    df = pd.DataFrame(list(group_costs.items()), columns=['Group Name', facility])
    return df



def download_report_group(request):
    # Get report type and dates from the request
    report_type = request.GET.get('reportType')
    start_date = request.GET.get('startDateGroup')
    end_date = request.GET.get('endDateGroup')
    group_name = request.GET.get('groupName')
    #print('groupName', group_name, 'type: ', report_type, 'start: ', start_date, 'end: ', end_date)
    
    if group_name == "Select Group":
            messages.error(request, "Please select an item from the dropdown menu.")
            return redirect('CalendarApp:reports_view')        

    df1, df2 = generate_report_dataframe_group(group_name, report_type, start_date, end_date)
    if (df1.empty or df2.empty) :
            messages.error(request, "There are no expenses to report. Please select another group or sets of dates")
            return redirect('CalendarApp:reports_view')

    messages.success(request, '')
                     #"Expense summary report is being generated and will be available for download shortly.")
    fname="report.xlsx"
    response = HttpResponse(content_type='application/xlsx')
    response['Content-Disposition'] = f'attachment; filename={fname}'
    
    with pd.ExcelWriter(response) as writer:
        df2.to_excel(writer, sheet_name='Cost Summary', index=False)
        df1.to_excel(writer, sheet_name='Detailed Expenses', index=False)

    return response


def generate_report_dataframe_group(group_name, report_type, start_date, end_date):
    # Get UserProfile instances for the specified group
    user_profiles = UserProfile.objects.filter(group__group_name=group_name)

    if report_type == 'userDefinedTime':
        start=datetime.strptime(start_date, '%Y-%m-%d')
        end=datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end=timezone.now()
        start=end - timedelta(days=90)
        #print('LAST 3 MONTHS= ' + start.strftime("%d-%b-%Y") + ' to ' + end.strftime("%d-%b-%Y"))


    # Initialize an empty list to store dictionaries for each row
    report_data = []

    for user_profile in user_profiles:
        # Get Booking instances for the user_profile
        usn=user_profile.user.username
        ln = user_profile.user.last_name
        external=user_profile.is_external
        bookings = Booking.objects.filter(username=usn,
                                          booked_start_date__date__gte=start.date(),
                                          booked_end_date__date__lte=end.date()
                                         )

        for booking in bookings:
            # Calculate the duration by subtracting booked_end_date from booked_start_date
            duration_timedelta = booking.booked_end_date - booking.booked_start_date
            duration_hours = duration_timedelta.total_seconds() / 3600

            try:
                # Get the group name for the user associated with the booking
                external = user_profile.is_external
                mb = user_profile.group.machines_bought
                buyer = False
                #check if the user of this booking has ever bought machines
                if (mb.count() != 0):
                    thisBookedMachine = booking.machine_obj
                    #search if the machine of this booking is present
                    #    in the list of machines bought by the user
                    buyer = user_profile.group.machines_bought.filter(pk=thisBookedMachine.pk).exists()
            except UserProfile.DoesNotExist:
                external = buyer = False            
                
            # Calculate the total cost based on the machine type (assisted or external)
            if (booking.is_assisted):
                if buyer:
                    cost_field='hourly_cost_buyer_assisted'
                elif external:
                    cost_field='hourly_cost_external_assisted'
                else:
                    cost_field='hourly_cost_assisted'
            else:
                if buyer:
                    cost_field='hourly_cost_buyer'                    
                elif external:
                    cost_field='hourly_cost_external'
                else:
                    cost_field='hourly_cost'

            hourly_cost = float(getattr(booking.machine_obj, cost_field))

            total_cost = hourly_cost * duration_hours

            # Append a dictionary with the required data to the report_data list
            report_data.append({
                'user': usn,
                'last name': ln, 
                'service': booking.machine_obj.machine_name,
                'facility': booking.machine_obj.facility,
                'date': booking.booked_start_date.strftime("%d-%b-%Y"),
                'hourly cost': hourly_cost,
                'hours': duration_hours,
                'total cost': total_cost,
            })

    # Create a DataFrame from the list of dictionaries
    report_df = pd.DataFrame(report_data)
    result_df = pd.DataFrame() #define result_df so that it can be returned in case of an empty report_df
    
    if report_df.empty : return report_df, result_df
    
    sum_total_cost_df = report_df.groupby('facility')['total cost'].sum().reset_index()
    # Add an extra header for group_name and timeframe analyzed
    timeframe_analyzed = start.strftime("%d-%b-%Y") + ' to ' + end.strftime("%d-%b-%Y")
    
    # Create a new DataFrame with a single row containing the extra information
    extra_info_df = pd.DataFrame([[group_name, timeframe_analyzed]], columns=['Group Name', 'Timeframe Analyzed'])
    
    # Concatenate the DataFrames along columns
    result_df = pd.concat([extra_info_df, sum_total_cost_df], axis=1)

    return report_df, result_df


def machines(request):
    return HttpResponse("Machines web page.")
    #return redirect('home')

def reports_view(request):
    # Get distinct group names
    distinct_groups = MBCGroup.objects.values_list('group_name', flat=True)

    context = {'distinct_groups': distinct_groups}
    return render(request, 'CalendarApp/reports_view.html', context)



###########################################################################################################################
#                                                                                                                         #
#                                               Manage display of bookings                                                #
#                                                                                                                         #
###########################################################################################################################
 

def calendar_view(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    machine2Book_name = str(user_profile.preferred_machine_name)
    machine2Book_obj = Machine.objects.get(machine_name=machine2Book_name)
    current_facility = machine2Book_obj.facility
    machine2Book_timelimit = machine2Book_obj.max_booking_duration
    #line to remove when database is updated
    if (machine2Book_timelimit == None): machine2Book_timelimit = 0
    
    machines_allowed = user_profile.machines4ThisUser.all()
    #now prepare 2 lists of strings
    facilities4ThisUser = [m for m in set(str(machine.facility) for machine in machines_allowed)]
    otherMachinesInCurrentFacility = [str(machine.machine_name) for machine in machines_allowed if machine.facility == current_facility]
    
    context = prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, machine2Book_timelimit, otherMachinesInCurrentFacility)
    context['facility_usage_dict'] = calculate_percentage_of_workingday(user_profile, current_facility, timezone.now())
    return render(request, 'CalendarApp/week_view.html', context)


def prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, timelimit, otherMachinesInCurrentFacility):
    
    #prepare bookings as Json object
    formatted_bookings_json = JsonFormattedBookings(user, machine2Book_name)
    
    #print('JSON formatting timelimit: ', timelimit, ' timelimit string:', str(timelimit))
    context = {
        'username': user.username,
        'groupname': user_profile.group.group_name,
        'facilityname': current_facility,
        'facilities4ThisUser' : facilities4ThisUser,
        'machine2BookName': machine2Book_name,
        'timelimit' : str(timelimit),
        'otherMachinesInCurrentFacility': otherMachinesInCurrentFacility,
        'formatted_bookings_json': formatted_bookings_json,
    }
    return context

def JsonFormattedBookings(user, machine2Book_name):
    current_datetime = timezone.now()    
    days = get_previous_sunday_and_next_saturday(current_datetime)
    #three_months_later_datetime = current_datetime + timedelta(days=90)  # Assuming 30 days per month
    three_months_later_datetime = days['sun'] + timedelta(days=90)  # Assuming 30 days per month

    # Retrieve upcoming_bookings queryset for dates within the next 3 months
    upcoming_bookings = Booking.objects.filter(
        booked_start_date__gt=days['sun'],
        booked_start_date__lte=three_months_later_datetime,
        machine_obj__machine_name=machine2Book_name
    )
    # Create a list to hold JSON objects for each booking
    formatted_bookings = []
    #print("formatted_bookings: ", formatted_bookings, "\n")

    # Iterate through the upcoming bookings and format them as JSON
    for booking in upcoming_bookings:
        formatted_booking = {
            "title": booking.title,
            "start": booking.booked_start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "end": booking.booked_end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "editable": False,          # requied to make the event not resizable/draggable n1
            "durationEditable": False,  # requied to make the event not resizable/draggable n2
            "color" : "#007BFF" #"dodgerblue"
        }
        if booking.username != user.username :
            formatted_booking["color"] = "grey"
        if booking.booked_start_date < current_datetime:
            if formatted_booking["color"] == "grey":
                formatted_booking["color"]="lightgrey"
            else:
                formatted_booking["color"]="LightSteelBlue"

        formatted_bookings.append(formatted_booking)
    # Convert the list of formatted bookings to a JSON object
    formatted_bookings_json = json.dumps(formatted_bookings, ensure_ascii=False)
    return formatted_bookings_json



###########################################################################################################################
#                                                                                                                         #
#                                                 Add/delete/move booking                                                 #
#                                                                                                                         #
###########################################################################################################################
    

def add_booking(request):
    dt = request.GET.get("start", None)
    start = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z")
    dt = request.GET.get("end", None)
    end = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z")
    machine2Book_name = str(request.GET.get("currentmachine", None))
    title = request.GET.get("title", None)
    assistance = request.GET.get("assistance", None)
    assistance = (assistance == "yes")
    
    
    user = request.user
    username = user.username
    user_profile = UserProfile.objects.get(user=user)
    machine2Book = user_profile.machines4ThisUser.get(machine_name=machine2Book_name)

    # Check for overlapping events
    overlapping_events = Booking.objects.filter(
        machine_obj=machine2Book,
        booked_start_date__lt=end,
        booked_end_date__gt=start
    )
    
    if overlapping_events.exists():
        #print('add impossible!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        formatted_bookings_json = JsonFormattedBookings(user, machine2Book_name)
        context = {
            'status': 'error',
            'message': 'Overlap with existing event detected.  Your calendar page will be updated.',
            'formatted_bookings_json': formatted_bookings_json,
        }
        return JsonResponse(context, safe=False, status=400)

    # Create and save the event    
    event = Booking(username=username,
                    title=str(title),
                    machine_obj=machine2Book,
                    booked_start_date=start,
                    booked_end_date=end,
                    is_assisted = assistance,
                    duration=1)
    
    event.save()
    return JsonResponse({"status": "success"})


def del_booking(request):
    machine2Book_name = str(request.GET.get("currentmachine", None))
    dt = request.GET.get("start", None)
    start = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z")

    title = str(request.GET.get("title", None))

    user = request.user
    username = str(user.username)
    #user_profile = UserProfile.objects.get(user=user)

    b = Booking.objects.filter(
         booked_start_date=start,
         username=username,
         title=title,
         machine_obj__machine_name=machine2Book_name,
        )
    if b.count() == 1 :
        booking=b.get()
        #print("booking DELETED: ", booking)
        booking.delete()
        return JsonResponse({"status": "success"})
    else:
        #print("delete failed")    
        formatted_bookings_json = JsonFormattedBookings(user, machine2Book_name)
        context = {
            'status': 'error',
            'message': 'Attempting to delete a non-existent event.  Your calendar page will be updated.',
            'formatted_bookings_json': formatted_bookings_json,
        }
        return JsonResponse(context, safe=False, status=400)


def move_booking(request):    
    machine2Book_name = str(request.GET.get("currentmachine", None))
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    machine2Book = user_profile.machines4ThisUser.get(machine_name=machine2Book_name)
    
    newStartStr = request.GET.get("newStart", None)
    newStart = datetime.strptime(newStartStr, "%Y-%m-%dT%H:%M:%S%z")
    newEndStr = request.GET.get("newEnd", None)
    newEnd = datetime.strptime(newEndStr, "%Y-%m-%dT%H:%M:%S%z")
    oldStartStr = request.GET.get("oldStart", None)
    oldStart = datetime.strptime(oldStartStr, "%Y-%m-%dT%H:%M:%S%z")
    #print("newStartStr: ", newStartStr, " newStart: ", newStart, " newEndStr: ", newEndStr,
    #     " oldStartStr: ", oldStartStr, " oldStart: ", oldStart)
    
    # Check for overlapping events
    overlapping_events = Booking.objects.filter(
        machine_obj=machine2Book,
        booked_start_date__lt=newEnd,
        booked_end_date__gt=newStart
    ).exclude(
        booked_start_date=oldStart  # Exclude events with the same start date as the dragged event
    )
    
    if overlapping_events.exists():
        formatted_bookings_json = JsonFormattedBookings(user, machine2Book_name)
        context = {
            'status': 'error',
            'message': 'Overlap with existing event detected.  Your calendar page will be updated.',
            'formatted_bookings_json': formatted_bookings_json,
        }
        return JsonResponse(context, safe=False, status=400)
    
    # Retrieve the Booking object
    usn=request.user.username
    obj = Booking.objects.get(username=usn,
                              machine_obj__machine_name=machine2Book_name,
                              booked_start_date=oldStart)
    
    # Update the Booking object
    obj.booked_start_date = newStart
    obj.booked_end_date = newEnd
    
    # Save changes to the database
    obj.save()
    
    return JsonResponse({"status": "success"})



###########################################################################################################################
#                                                                                                                         #
#                                                 machine/facility buttons                                                #
#                                                                                                                         #
###########################################################################################################################
    

def next_machine(request):
    current_machine_name = str(request.GET.get("currmachine", None))
    current_machine = Machine.objects.get(machine_name=current_machine_name)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    machines_allowed = user_profile.machines4ThisUser.all()
    current_facility = current_machine.facility
    facilities4ThisUser = [m for m in set(str(machine.facility) for machine in machines_allowed)]
    otherMachinesInCurrentFacility = [str(machine.machine_name) for machine in machines_allowed if machine.facility == current_facility]

    current_index = otherMachinesInCurrentFacility.index(current_machine_name)
    next_index = (current_index + 1) % len(otherMachinesInCurrentFacility)
    machine2Book_name = otherMachinesInCurrentFacility[next_index]
    next_machine_obj = Machine.objects.get(machine_name=machine2Book_name)
    timelimit = next_machine_obj.max_booking_duration
    #print('next_machine->machine2Book_name: ', machine2Book_name)
    #print('next_machine->timelimit', timelimit)
    
    #line to remove when database is updated:
    if (timelimit == None): timelimit = 0

    
    context = prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, timelimit, otherMachinesInCurrentFacility)
    json_data = json.dumps(context, ensure_ascii=False)
    return JsonResponse(json_data, safe=False)


def previous_machine(request):
    current_machine_name = str(request.GET.get("currmachine", None))
    current_machine = Machine.objects.get(machine_name=current_machine_name)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    machines_allowed = user_profile.machines4ThisUser.all()
    current_facility = current_machine.facility
    facilities4ThisUser = [m for m in set(str(machine.facility) for machine in machines_allowed)]
    otherMachinesInCurrentFacility = [str(machine.machine_name) for machine in machines_allowed if machine.facility == current_facility]

    current_index = otherMachinesInCurrentFacility.index(current_machine_name)
    next_index = (current_index - 1) % len(otherMachinesInCurrentFacility)
    machine2Book_name = otherMachinesInCurrentFacility[next_index]
    previous_machine_obj = Machine.objects.get(machine_name=machine2Book_name)
    timelimit = previous_machine_obj.max_booking_duration
    #print('previous_machine->machine2Book_name: ', machine2Book_name)
    #print('previous_machine->timelimit', timelimit)
        
    #line to remove when database is updated:
    if (timelimit == None): timelimit = 0
    
    context = prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, timelimit, otherMachinesInCurrentFacility)
    json_data = json.dumps(context, ensure_ascii=False)
    return JsonResponse(json_data, safe=False)


def select_machine(request):
    machine2Book_name = str(request.GET.get("selecteditem", None))
    current_machine = Machine.objects.get(machine_name=machine2Book_name)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    machines_allowed = user_profile.machines4ThisUser.all()
    current_facility = current_machine.facility
    facilities4ThisUser = [m for m in set(str(machine.facility) for machine in machines_allowed)]
    otherMachinesInCurrentFacility = [str(machine.machine_name) for machine in machines_allowed if machine.facility == current_facility]
    timelimit = current_machine.max_booking_duration
    #print('select_machine->machine2Book_name: ', machine2Book_name)
    #print('select_machine->timelimit', timelimit)
    
    #line to remove when database is updated:
    if (timelimit == None): timelimit = 0
    
    context = prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, timelimit, otherMachinesInCurrentFacility)
    json_data = json.dumps(context, ensure_ascii=False)
    return JsonResponse(json_data, safe=False)


def select_facility(request):
    current_facility = str(request.GET.get("selecteditem", None))
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    start = str(request.GET.get("start", None))
    date = datetime.fromisoformat(start[:-1]) #it seems the final Z in the str is not recognized

    machines_allowed = user_profile.machines4ThisUser.all()
    facilities4ThisUser = [m for m in set(str(machine.facility) for machine in machines_allowed)]
    otherMachinesInCurrentFacility = [str(machine.machine_name) for machine in machines_allowed if machine.facility == current_facility]
    machine2Book_name = otherMachinesInCurrentFacility[0] #arbitraly select the machine in pos[0] to start with
    current_machine = Machine.objects.get(machine_name=machine2Book_name)
    timelimit = current_machine.max_booking_duration
    #print('select_facility->machine2Book_name: ', machine2Book_name)
    #print('select_facility->timelimit', timelimit)

    #line to remove when database is updated:
    if (timelimit == None): timelimit = 0
    

    usage_dict = calculate_percentage_of_workingday(user_profile, current_facility, date)
    
    context = prepare_bookings(user, user_profile, current_facility, facilities4ThisUser, machine2Book_name, timelimit, otherMachinesInCurrentFacility)
    context['usage_dict'] = usage_dict
    
    json_data = json.dumps(context, ensure_ascii=False)
    return JsonResponse(json_data, safe=False)



###########################################################################################################################
#                                                                                                                         #
#                                         Calculate facility usage machine by machine                                     #
#                                                                                                                         #
###########################################################################################################################
    

def calculate_percentage_of_workingday(user_profile, target_facility, day):
#def calculate_percentage_of_workingday(target_facility, day):
    dates = get_previous_sunday_and_next_saturday(day)
    
    # Get the machines in the specified facility that are allowed for the user
    machines_in_facility = Machine.objects.filter(
            facility=target_facility,
            id__in=user_profile.machines4ThisUser.values_list('id', flat=True)
        ).prefetch_related(
                    Prefetch('booking_set', queryset=Booking.objects.filter(
                        booked_start_date__date__gte=dates['sun'].date(),
                        booked_end_date__date__lte=dates['sat'].date()
                ), to_attr='filtered_bookings')
            )
    
    # Create a dictionary to store daily_usage_in_a_week for each machine
    facility_usage_dict = {}
    
    # Iterate over machines in the facility
    for machine in machines_in_facility:
        # Get the machine name
        machine_name = machine.machine_name
    
        # Initialize daily_usage_in_a_week list with zeros
        daily_usage_in_a_week = [0] * 7
    
        # Iterate over the filtered bookings for the machine
        for booking in machine.filtered_bookings:
            day_of_week = (booking.booked_start_date.weekday() + 1) % 7  # Adjust so that Sunday is accessed by [0]
            total_hours = (booking.booked_end_date - booking.booked_start_date).total_seconds() / 3600 * 100 / 12 #calculate % in hours over 1/2 a day
            daily_usage_in_a_week[day_of_week] += total_hours
    
        # Add the machine's daily_usage_in_a_week to the dictionary
        #print(machine_name, daily_usage_in_a_week)
        facility_usage_dict[machine_name] = daily_usage_in_a_week

    return facility_usage_dict


def machines_usage(request):
    start = str(request.GET.get("start", None))
    date = datetime.fromisoformat(start[:-1]) #it seems the final Z in the str is not recognized

    facility = str(request.GET.get("facility", None))    
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    #day=datetime.strptime("Sun Dec 03 2023", "%a %b %d %Y") #this is the format from toDateString in Fullcalendar JS
    days = get_previous_sunday_and_next_saturday(date)

    context = calculate_percentage_of_workingday(user_profile, facility, days['sun'])
    return JsonResponse(context, safe=False)



###########################################################################################################################
#                                                                                                                         #
#                                                        Utilities                                                        #
#                                                                                                                         #
###########################################################################################################################
    

def get_previous_sunday_and_next_saturday(specific_date):
    # Find the previous Sunday; specific_date is a Datetime object
    idx=(specific_date.weekday()+1)%7
    sun = specific_date - timedelta(days=idx)
    # Find the next Saturday
    sat=sun + timedelta(days=6)
    dates={'sat': sat, 'sun': sun}
    return dates



