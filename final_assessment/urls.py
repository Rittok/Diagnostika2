from django.urls import path
from .views import start_final_assessment, assessment_results

app_name = 'final_assessment'

urlpatterns = [
    path('start/', start_final_assessment, name='start-final-assessment'),
    path('results/', assessment_results, name='assessment-results'),
]