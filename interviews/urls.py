# interviews/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/',views.upload,name='upload'),
    path('form/',views.form,name='form'),
    path('analyse/', views.initiate_analysis, name='initiate_analysis'), 
    path('processing/', views.display_processing_screen, name='display_processing_screen'), 
    path('check_status/', views.check_analysis_status, name='check_analysis_status'), 
    path('results/<int:session_id>/', views.show_results_report, name='show_results_report'), 
    path('error/', views.show_upload_error, name='show_upload_error'),
]