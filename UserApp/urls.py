from django.urls import path
from . import views
#from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.home, name='home'),
    #path('login/', LoginView.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('reports/', views.reports, name='reports'),
]
