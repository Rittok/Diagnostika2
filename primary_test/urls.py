from django.urls import path
from .views import *

app_name = 'primary_test'

urlpatterns = [
    path('start/', start_primary_diagnostic, name='start_primary_diagnostic'),
    path('test/', primary_diagnostic_view, name='primary_diagnostic'),
    path('results/<str:percent>/', diagnostic_results, name='diagnostic_results'),
]