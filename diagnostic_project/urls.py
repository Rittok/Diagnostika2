from django.urls import include, path
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('diagnostic/', include(('diagnostic.urls', 'diagnostic'), namespace='diagnostic')),
    path('', include(('primary_test.urls','primary_test'),namespace = 'primary_test')),  
    path('intermediate_test/', include(('intermediate_test.urls','intermediate_test'),namespace ='intermediate_test')), 
    path('final_assessment/', include(('final_assessment.urls', 'final_assessment'),namespace = 'final_assessment')),
    
]
