from django.urls import path
from apps.log_app.views import DailyLogView

urlpatterns = [
    path('daily-log/', DailyLogView.as_view(), name='daily-log'),
]