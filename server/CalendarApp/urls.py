from django.urls import path
from . import views

app_name = 'CalendarApp'

urlpatterns = [
    path('calendar_view', views.calendar_view, name='calendar_view'), #no / at the end otherwise it skips to subdirectory and JS does not find views
    path('machines/', views.machines, name='machines'),
    path('add_booking/', views.add_booking, name='add_booking'),
    path('del_booking/', views.del_booking, name='del_booking'), 
    path('move_booking/', views.move_booking, name='move_booking'), 
    path('previous_machine/', views.previous_machine, name='previous_machine'), 
    path('next_machine/', views.next_machine, name='next_machine'), 
    path('select_machine/', views.select_machine, name='select_machine'), 
    path('select_facility/', views.select_facility, name='select_facility'), 
    path('machines_usage/', views.machines_usage, name='machines_usage'),
    path('reports_view', views.reports_view, name='reports_view'), #no / at the end otherwise it skips to subdirectory and JS does not find views
    path('download_report_group/', views.download_report_group, name='download_report_group'),
    path('download_report_facilities/', views.download_report_facilities, name='download_report_facilities'),

]
