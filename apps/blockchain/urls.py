from django.urls import path
from . import views

urlpatterns = [
    path('', views.blockchain_explorer_view, name='blockchain_explorer'),
]
