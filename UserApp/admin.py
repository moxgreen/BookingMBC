from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'group_name', 'is_external')  # Display these fields in the admin list view
    list_filter = ('group_name',)  # Add a filter for group_name

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # Check if the response is an instance of TemplateResponse
        if isinstance(response, TemplateResponse):
            # Add a custom context variable to display unique group names
            response.context_data['unique_groups'] = UserProfile.objects.values('group_name').annotate(total=Count('group_name'))
        return response

admin.site.register(UserProfile, UserProfileAdmin)
