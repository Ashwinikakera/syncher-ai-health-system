from django.urls import path
from apps.log_app.views import DailyLogView, CycleLogView

urlpatterns = [
<<<<<<< HEAD
    path('daily-log', DailyLogView.as_view(), name='daily-log'),
=======
    path('daily-log/',  DailyLogView.as_view(),  name='daily-log'),
    path('cycle-log/',  CycleLogView.as_view(),  name='cycle-log'),
>>>>>>> d98ae17 (dev 1 editing done)
]