from django.urls import path
from . import views

urlpatterns = [
    path('', views.start_primary_diagnostic, name='start_primary_diagnostic'),
]