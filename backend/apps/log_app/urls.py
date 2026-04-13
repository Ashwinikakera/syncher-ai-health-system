from django.urls import path
from apps.log_app.views import DailyLogView, CycleLogView

#paths for cycle log and daily log
urlpatterns = [
    path('daily-log/',  DailyLogView.as_view(),  name='daily-log'),
    path('cycle-log/',  CycleLogView.as_view(),  name='cycle-log'),
]
