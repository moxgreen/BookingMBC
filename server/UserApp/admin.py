from django.contrib import admin, messages
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, MBCGroup
from CalendarApp.models import Machine


import pandas as pd
import re
import io

from django.urls import path
from django.shortcuts import render
from django import forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.db import IntegrityError
from django.db import transaction




@transaction.atomic
def clear_machines_for_all_users():
    # Fetch all UserProfile objects
    user_profiles = UserProfile.objects.all()

    # Loop through UserProfile objects
    for user_profile in user_profiles:
        # Clear the related machines4ThisUser queryset
        user_profile.machines4ThisUser.clear()


class UserExcelImportForm(forms.Form):
    excel_upload = forms.FileField()


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_group_name', 'is_external')  # Display these fields in the admin list view
    list_filter = ('group__group_name', 'is_external')  # Add a filter for group_name
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'group__group_name']  # Add this line to enable search by username

    def get_group_name(self, obj):
        return obj.group.group_name if obj.group else ''

    get_group_name.short_description = 'Group Name'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'machines4ThisUser':
            kwargs['queryset'] = db_field.remote_field.model.objects.order_by('machine_name')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        new_urls1 = [path('upload-users/', self.upload_users),]
        new_urls2 = [path('download-users/', self.download_users),]
        new_urls3 = [path('upload-permissions/', self.upload_permissions),]
        new_urls4 = [path('download-permissions/', self.download_permissions),]
        return new_urls1 + new_urls2 + new_urls3 + new_urls4 + urls


    def upload_users(self, request):
        if request.method == "POST":
            excel_file = request.FILES.get("excel_upload")
            # Call the function to clear machines4ThisUser for all users
            #clear_machines_for_all_users()

            if not excel_file.name.endswith(('.xls', '.xlsx')):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            try:
                # Read the Excel file into a DataFrame
                excel_data = pd.read_excel(excel_file)
                errors=False
                non_existent_users=''
                
                # Iterate through the rows of the DataFrame
                for index, row in excel_data.iterrows():
                    # Retrieve values from the DataFrame
                    username = row['user name']
                    first_name = row['first fname']
                    last_name = row['last name']
                    email = row['email']
                    preferred_machine_name = row['preferred machine']
                    is_external = row['external']
                
                   # Try to get UserProfile instance based on username
                    try:
                        user_profile = UserProfile.objects.get(user__username=username)
                
                        # Update UserProfile instance
                        user_profile.user.first_name = first_name
                        user_profile.user.last_name = last_name
                        user_profile.user.email = email
                        user_profile.preferred_machine_name = preferred_machine_name
                        user_profile.is_external = is_external
                
                        # Save the changes
                        user_profile.user.save()
                        user_profile.save()
                
                    except UserProfile.DoesNotExist:
                        # Handle the case where the UserProfile instance does not exist
                        errors=True
                        if non_existent_users == '': 
                            non_existent_users += username
                        else:
                            non_existent_users += ','+ username
                        continue
                
                txt='Excel file uploaded successfully'
                if errors:
                    txt += f' but some users where not inserted (like: {non_existent_users})'
                messages.success(request, txt)
                return HttpResponseRedirect(request.path_info)

            except Exception as e:
                messages.error(request, f'Error opening the Excel file: {e}')
                return HttpResponseRedirect(request.path_info)

        form = UserExcelImportForm()  # Assume you have a form for file uploads
        data = {"form": form}
        return render(request, "admin/excel_upload.html", data)


    def download_users(self, request):
        # Fetch all UserProfile objects
        user_profiles = UserProfile.objects.all()
        users = []
        
        # Loop through UserProfile objects
        for user_profile in user_profiles:
            # build a dict
            users_dict={
                'user name' : user_profile.user.username,
                'first fname' : user_profile.user.first_name,
                'last name' : user_profile.user.last_name,
                'email' : user_profile.user.email,
                'preferred machine' :  user_profile.preferred_machine_name,
                'external' : user_profile.is_external,
                }
            users.append(users_dict)
        
        data=pd.DataFrame(users)
        # Create Excel file in memory
        excel_file = io.BytesIO()

        # Use ExcelWriter to set column widths
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            data.to_excel(writer, sheet_name='users', index=False)

            # Access the XlsxWriter worksheet object
            worksheet = writer.sheets['users']

            # Iterate through each column and set the width based on the maximum length of the column data
            for i, col in enumerate(data.columns):
                max_len = max(data[col].astype(str).apply(len).max(), len(col))
                worksheet.set_column(i, i, max_len + 2)  # Add a little extra space

        excel_file.seek(0)

        # Prepare response for download
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=users.xlsx'
        response.write(excel_file.read())

        return response



    def upload_permissions(self, request):
        if request.method == "POST":
            excel_file = request.FILES.get("excel_upload")
            # Call the function to clear machines4ThisUser for all users
            #clear_machines_for_all_users()

            if not excel_file.name.endswith(('.xls', '.xlsx')):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            try:
                # Read the Excel file into a DataFrame
                df = pd.read_excel(excel_file)

                df=df.astype(object)
                df.fillna('', inplace=True) #fill first with a string compatible datatype 
                errors=False
                non_existent_data=''
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
                
                # Iterate over columns using iteritems
                for mn in df.columns:
                    #print(f"Machine: {mn}")
                    
                    # Iterate over rows for each column
                    for s in df[mn]:
                        # Use re.search to find the first email address in the input string
                        match = re.search(email_pattern, s)
                        # If a match is found, return the extracted email address; otherwise, return None
                        ema = match.group() if match else ""
                        if ema == "": continue
                        #print(f"  User email: {ema}")
                        try:
                            usp=UserProfile.objects.get(user__email=ema)
                        except UserProfile.DoesNotExist:
                            #print(f"  email not registered: {ema}")
                            errors=True
                            if non_existent_data == '': 
                                non_existent_data += ' email: ' + ema
                            else:
                                non_existent_data += ', email: ' + ema
                            continue
                        try:
                            m=Machine.objects.get(machine_name=mn)
                        except Machine.DoesNotExist:
                            #print(f"  machine not existent: {mn}")
                            errors=True
                            if non_existent_data == '': 
                                non_existent_data += ' machine: ' + mn
                            else:
                                non_existent_data += ', machine: ' + mn
                            break                            
                        try:
                            usp.machines4ThisUser.add(m)
                            usp.save()
                        except IntegrityError as e:
                            messages.error(request, f'Error {e} processing machines for {ema}')
                            return HttpResponseRedirect(request.path_info)
                        
                txt='Excel file uploaded successfully'
                if errors:
                    txt += f' but some data were missing (like: {non_existent_data})'
                messages.success(request, txt)
                return HttpResponseRedirect(request.path_info)

            except Exception as e:
                messages.error(request, f'Error opening the Excel file: {e}')
                return HttpResponseRedirect(request.path_info)

        form = UserExcelImportForm()  # Assume you have a form for file uploads
        data = {"form": form}
        return render(request, "admin/excel_upload.html", data)


    def download_permissions(self, request):
        # Create an empty DataFrame
        machine_email_dict={}
        
        # Fetch all UserProfile objects
        user_profiles = UserProfile.objects.all()
    
        # Loop through UserProfile objects
        for user_profile in user_profiles:
            # Extract email from user
            email = user_profile.user.email
            # Extract the names of the machines listed in the ManyToMany relation
            machines_list = [machine.machine_name for machine in user_profile.machines4ThisUser.all()]
            #loop through these machine names
            for machine_name in machines_list:
                if machine_name not in machine_email_dict:
                    #create a new column if machine_name column not yet generated
                    machine_email_dict[machine_name] = []
                machine_email_dict[machine_name].append(email)    
        # Find the maximum number of values for any key
        max_values = max(len(values) for values in machine_email_dict.values())

        # Normalize the number of values for each key otherwise pandas dataframe will not work
        for key, values in machine_email_dict.items():
            # Pad the list with "" to match the maximum number of values
            machine_email_dict[key] += [""] * (max_values - len(values))

        data = pd.DataFrame(machine_email_dict)

        # Create Excel file in memory
        excel_file = io.BytesIO()

        # Use ExcelWriter to set column widths
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
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
        response['Content-Disposition'] = 'attachment; filename=machines4users.xlsx'
        response.write(excel_file.read())

        return response

            




class InitialLetterFilter(admin.SimpleListFilter):
    title = _('Initial Letter')
    parameter_name = 'initial'

    def lookups(self, request, model_admin):
        # Get the distinct initial letters in the group names
        group_names = MBCGroup.objects.values_list('group_name', flat=True)
        initial_letters = set(name[0].upper() for name in group_names if name)
        return [(letter, letter) for letter in sorted(initial_letters)]

    def queryset(self, request, queryset):
        if self.value():
            # Filter groups based on the selected initial letter
            return queryset.filter(group_name__startswith=self.value())
        return queryset


class MBCGroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'location')
    list_filter = (InitialLetterFilter, 'location') #add list filters
    search_fields = ['group_name']  # Add this line to enable search by username
    ordering = ['group_name']  # Add ordering by group_name

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        # Check if the response is an instance of TemplateResponse
        if isinstance(response, TemplateResponse):
            # Add a custom context variable to display unique group names
            response.context_data['locations'] = MBCGroup.objects.values_list('location', flat=True).distinct()
        
        return response
        
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'machines_bought':
            kwargs['queryset'] = db_field.remote_field.model.objects.order_by('machine_name')
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MBCGroup, MBCGroupAdmin)
