from django.urls import path
from apps.auth_app.views import RegisterView, LoginView, OnboardingView

# urls for register login/onboarding

urlpatterns = [
    path('register/',    RegisterView.as_view(),    name='register'),
    path('login/',       LoginView.as_view(),       name='login'),
    path('onboarding/',  OnboardingView.as_view(),  name='onboarding'),
]