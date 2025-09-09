from django.urls import path
from .views import *


app_name = 'primary_test'

urlpatterns = [
    path('test/', test_page_view, name='test'),
    path('start-primary-diagnostic/', start_primary_diagnostic, name='start_primary_diagnostic'),
    path('block-test/<int:block_num>/', block_test_view, name='block_test'),
    path('diagnostic-results/', diagnostic_results, name='diagnostic_results'),
]