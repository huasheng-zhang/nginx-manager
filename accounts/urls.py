from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile_view, name='profile'),
    path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
    path('', views.DashboardView.as_view(), name='home'),
]
