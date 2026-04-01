from django.urls import path
from apps.dashboard_app.views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]