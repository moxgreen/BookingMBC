from django.urls import path
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView
from . import views
#from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.home, name='home'),
    #path('login/', LoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('reports/', views.reports, name='reports'),
    
    path('reset_password/', CustomPasswordResetView.as_view(), name='reset_password'),
    path('reset/<str:uidb64>/<str:token>/', CustomPasswordResetConfirmView.as_view(), name='custom_password_reset_confirm'),
]

