from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, MBCGroup

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_group_name', 'is_external')  # Display these fields in the admin list view
    list_filter = ('group__group_name', 'is_external')  # Add a filter for group_name
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'group__group_name']  # Add this line to enable search by username

    def get_group_name(self, obj):
        return obj.group.group_name if obj.group else ''

    get_group_name.short_description = 'Group Name'


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
        


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MBCGroup, MBCGroupAdmin)
