from django.urls import path
from apps.auth_app.views import RegisterView, LoginView, OnboardingView

urlpatterns = [
<<<<<<< HEAD
    path('register', RegisterView.as_view(), name='register'),
    path('login',    LoginView.as_view(),    name='login'),
=======
    path('register/',    RegisterView.as_view(),    name='register'),
    path('login/',       LoginView.as_view(),       name='login'),
    path('onboarding/',  OnboardingView.as_view(),  name='onboarding'),
>>>>>>> d98ae17 (dev 1 editing done)
]