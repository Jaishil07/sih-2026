from django.urls import path
from apps.ai_assistant.views import global_search_view

urlpatterns = [
    path('search/', global_search_view, name='global_search'),
]
