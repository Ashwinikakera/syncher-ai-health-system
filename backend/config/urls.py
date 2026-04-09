from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth — register, login
    path('api/', include('apps.auth_app.urls')),

    # Cycle logs
    path('api/', include('apps.cycle_app.urls')),

    # Daily logs
    path('api/', include('apps.log_app.urls')),

    # Dashboard
    path('api/', include('apps.dashboard_app.urls')),

    # Chatbot
    path('api/', include('apps.chatbot_app.urls')),

    #my-health
    path('api/', include('apps.health_app.urls')),
]