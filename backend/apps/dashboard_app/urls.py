from django.urls import path
from apps.dashboard_app.views import DashboardView

# dashboard path
urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]