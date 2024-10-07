from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Machine, Booking
from UserApp.models import UserProfile, Group

import pandas as pd
import io

from django.urls import path
from django.shortcuts import render
from django import forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse


class ExcelImportForm(forms.Form):
    excel_upload = forms.FileField()

###############################################################################
#                                  MachineAdmin                               #
###############################################################################

class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_name', 'facility')  # Display these fields in the admin list view
    list_filter = ('facility',)  # Add a filter for facility

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # Check if the response is an instance of TemplateResponse
        if isinstance(response, TemplateResponse):
            # Add a custom context variable to display unique facilities
            response.context_data['all_facilities'] = Machine.objects.values('facility').annotate(total=Count('facility'))

        return response
    
    def delete_queryset(self, request, queryset):
        # navigate the selected Machines to delete
        for obj in queryset:
            # Update UserProfile instances with preferred_machine_name equal to the machine_name of the Machine being deleted
            UserProfile.objects.filter(preferred_machine_name=obj.machine_name).update(preferred_machine_name="Seminar room")
            
            # Get all related UserProfiles using this machine to delete
            related_profiles = UserProfile.objects.filter(machines4ThisUser=obj)
             
            # Remove the machine being deleted from the machines4ThisUser field of all related UserProfiles
            for profile in related_profiles:
                 profile.machines4ThisUser.remove(obj)
    
        # Now delete all objects in the queryset
        queryset.delete()
    
        # Call the superclass method to perform the default delete operation
        super().delete_queryset(request, queryset)
        

    def delete_model(self, request, obj):
        # Update related fields to standard machine named "Seminar room"
        UserProfile.objects.filter(preferred_machine_name=obj.machine_name).update(preferred_machine_name="Seminar room")
        # Now delete the instances of machine to be delete where it appears in machines4ThisUser
        # 1) Get all related UserProfiles
        related_profiles = UserProfile.objects.filter(machines4ThisUser=obj)
         
        # 2) Remove the machine being deleted from the machines4ThisUser field of all related UserProfiles
        for profile in related_profiles:
             profile.machines4ThisUser.remove(obj)

        obj.delete()

    def get_urls(self):
        urls = super().get_urls()
        new_urls1 = [path('upload-excel/', self.upload_excel),]
        new_urls2 = [path('download-excel/', self.download_excel),]
        return new_urls1 + new_urls2 + urls

    def upload_excel(self, request):
        if request.method == "POST":
            excel_file = request.FILES.get("excel_upload")

            if not excel_file.name.endswith(('.xls', '.xlsx')):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            try:
                # Read the Excel file into a DataFrame
                df = pd.read_excel(excel_file)

                # Iterate through rows and create/update Machine objects
                for index, row in df.iterrows():
                    machine_data = {
                        'machine_name': row['machine_name'],
                        'facility': row['facility'],
                        'is_open': str(row['is_open']).lower() == "true" or str(row['is_open']).lower() == "vero",
                        'max_booking_duration': row['max_booking_duration'] if not pd.isna(row['max_booking_duration']) else 0,
                        'hourly_cost': row['hourly_cost'] if not pd.isna(row['hourly_cost']) else 0,
                        'hourly_cost_assisted': row['hourly_cost_assisted'] if not pd.isna(row['hourly_cost_assisted']) else 0,
                        'hourly_cost_external': row['hourly_cost_external'] if not pd.isna(row['hourly_cost_external']) else 0,
                        'hourly_cost_external_assisted': row['hourly_cost_external_assisted'] if not pd.isna(row['hourly_cost_external_assisted']) else 0,
                        'hourly_cost_buyer': row['hourly_cost_buyer'] if not pd.isna(row['hourly_cost_buyer']) else 0,
                        'hourly_cost_buyer_assisted': row['hourly_cost_buyer_assisted'] if not pd.isna(row['hourly_cost_buyer_assisted']) else 0,
                    }
                
                    Machine.objects.update_or_create(
                        machine_name=row['machine_name'],
                        defaults=machine_data
                    )

                messages.success(request, 'Excel file uploaded successfully')
                return HttpResponseRedirect(request.path_info)

            except Exception as e:
                messages.error(request, f'Error processing the Excel file: {e}')
                return HttpResponseRedirect(request.path_info)

        form = ExcelImportForm()  # Assume you have a form for file uploads
        data = {"form": form}
        return render(request, "admin/excel_upload.html", data)
    


    def download_excel(self, request):
        # Get all Machine objects
        machines = Machine.objects.all()

        # Specify the columns to include in the DataFrame (excluding 'id')
        columns_to_include = [field.name for field in Machine._meta.fields if field.name != 'id']
        
        # Convert QuerySet to DataFrame, including only specified columns
        data = pd.DataFrame(list(machines.values(*columns_to_include)))
        
        # Create Excel file in memory
        excel_file = io.BytesIO()

        # Use ExcelWriter to set column widths
        with pd.ExcelWriter(excel_file,
                            engine='xlsxwriter',
                            engine_kwargs={'options': {'strings_to_numbers': True}}) as writer:
            data.to_excel(writer, sheet_name='Machines', index=False)

            # Access the XlsxWriter worksheet object
            worksheet = writer.sheets['Machines']

            # Iterate through each column and set the width based on the maximum length of the column data
            for i, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).apply(len).max(), len(col))
                worksheet.set_column(i, i, max_len + 2)  # Add a little extra space

        excel_file.seek(0)

        # Prepare response for download
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=machines.xlsx'
        response.write(excel_file.read())

        return response

            

        
###############################################################################
#                                 GroupNameFilter                             #
###############################################################################

class GroupNameFilter(admin.SimpleListFilter):
    title = 'Group Name'
    parameter_name = 'group_name'

    def lookups(self, request, model_admin):
        return Group.objects.values_list('group_name', 'group_name')

    def queryset(self, request, queryset):
        if self.value():
            # Step 1: Filter UserProfile records
            user_profiles = UserProfile.objects.filter(
                group__group_name=self.value()
            )
    
            # Step 2: Get usernames from filtered UserProfiles
            usernames = user_profiles.values_list('user__username', flat=True)
    
            # Step 3: Filter Booking records based on obtained usernames
            return queryset.filter(username__in=usernames)
    
        return queryset
    

###############################################################################
#                                 BookingAdmin                                #
###############################################################################

class BookingAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_group_name', 'machine_obj', 'booked_start_date', 'is_assisted')
    list_filter = (GroupNameFilter, 'machine_obj__facility', 'is_assisted', 'booked_start_date')

    def get_group_name(self, obj):
        try:
            user_profile = UserProfile.objects.get(user__username=obj.username)
            return user_profile.group.group_name
        except UserProfile.DoesNotExist:
            return ''

    get_group_name.short_description = 'Group Name'
    #machine_obj.short_description = 'Machine'

    def get_group_name_choices(self, request, model_admin):
        return Group.objects.values_list('group_name', flat=True)


    def get_facility_choices(self, request, model_admin):
        return Machine.objects.values_list('facility', flat=True).distinct()

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        if isinstance(response, TemplateResponse):
            response.context_data['all_machines'] = Machine.objects.all()
            response.context_data['all_user_profiles'] = self.get_group_name_choices(request, self)
            response.context_data['all_dates'] = Booking.objects.annotate(date=TruncDate('booked_start_date')).values('date').distinct()
            response.context_data['all_facilities'] = self.get_facility_choices(request, self)

        return response


admin.site.register(Machine, MachineAdmin)
admin.site.register(Booking, BookingAdmin)




