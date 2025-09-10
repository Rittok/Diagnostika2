from django.urls import path
from .views import *

app_name = 'primary_test'

urlpatterns = [
    path('block/<int:block_num>/', block_test_view, name='block_test'),
    path('results/', diagnostic_results, name='diagnostic_results'),
    path('download-report/<str:username>/', download_report, name='download_report'),
]