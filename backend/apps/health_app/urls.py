from django.urls import path
from apps.health_app.views import MyHealthView

urlpatterns = [
    path('my-health/', MyHealthView.as_view(), name='my-health'),
]