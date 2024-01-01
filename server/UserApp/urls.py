from django.urls import path
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView, ServicesChangeView
from .views import CustomPasswordChangeView, CustomPasswordChangeDoneView
from . import views
#from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    #path('login/', LoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('reports/', views.reports, name='reports'),
    
    path('reset_password/', CustomPasswordResetView.as_view(), name='reset_password'),
    path('reset/<str:uidb64>/<str:token>/', CustomPasswordResetConfirmView.as_view(), name='custom_password_reset_confirm'),
    
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', CustomPasswordChangeDoneView.as_view(), name='custom_password_change_done'),

    path('services_change/', ServicesChangeView.as_view(), name='services_change'),
    
]

