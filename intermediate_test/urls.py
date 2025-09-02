from django.urls import path
from .views import start_intermediate_test, intermediate_results

app_name = 'intermediate_test'

urlpatterns = [
    path('start/', start_intermediate_test, name='start-intermediate-test'),
    path('results/', intermediate_results, name='intermediate-results'),
]