from django.contrib import admin
from django.template.response import TemplateResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Machine, Booking
from UserApp.models import UserProfile

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


class GroupNameFilter(admin.SimpleListFilter):
    title = 'Group Name'
    parameter_name = 'group_name'

    def lookups(self, request, model_admin):
        return UserProfile.objects.values_list('group_name', 'group_name').distinct()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                username__in =
                UserProfile.objects.filter(group_name=self.value()).values_list('user__username', flat=True)
            )
        return queryset


class BookingAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_group_name', 'machine_obj', 'booked_start_date', 'is_assisted')
    list_filter = (GroupNameFilter, 'machine_obj__facility', 'is_assisted', 'booked_start_date')

    def get_group_name(self, obj):
        try:
            user_profile = UserProfile.objects.get(user__username=obj.username)
            return user_profile.group_name
        except UserProfile.DoesNotExist:
            return ''

    get_group_name.short_description = 'Group Name'
    #machine_obj.short_description = 'Machine'

    def get_group_name_choices(self, request, model_admin):
        return UserProfile.objects.filter(
                user__username__in=
                Booking.objects.values_list('username', flat=True).distinct()
            ).values_list('group_name', flat=True).distinct()

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

