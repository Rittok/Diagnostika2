from django.urls import path,re_path
from .views import *

app_name = 'primary_test'

urlpatterns = [
    path('block1/page<int:page>/', block1_test_view, name='block1_test'),
    path('block2/', block2_test_view, name='block2_test'),
    path('results/', diagnostic_results, name='diagnostic_results'),
    path('download-report/<str:username>/', download_report, name='download_report'),
]