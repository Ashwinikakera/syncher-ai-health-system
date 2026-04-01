from django.urls import path
from apps.cycle_app.views import CycleView

urlpatterns = [
    path('cycle/', CycleView.as_view(), name='cycle'),
]