from django.urls import path
from . import views

urlpatterns = [
    path('registration/register/', views.registration_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('test_page/', views.test_page_view, name='test_page'), 
]