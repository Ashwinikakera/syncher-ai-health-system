from django.urls import path
from apps.user_app.views import OnboardingView

urlpatterns = [
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),
]