from django.urls import path
from apps.chatbot_app.views import ChatView

urlpatterns = [
    path('chat/', ChatView.as_view(), name='chat'),
]