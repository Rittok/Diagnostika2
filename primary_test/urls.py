from django.urls import path
from .views import *


app_name = 'primary_test'

urlpatterns = [
    path('primary_t/', primary_diagnostic_view, name='primary_t'),
    path('results/<str:percent>/', diagnostic_results, name='diagnostic_results'),
]