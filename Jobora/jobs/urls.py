from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Profile
    path('dashboard/', views.company_dashboard, name='company_dashboard'),
    path('edit-profile/', views.edit_company_profile, name='edit_company_profile'),
    
    # Job Management
    path('post-job/', views.post_job, name='post_job'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('toggle-job-status/<int:job_id>/', views.toggle_job_status, name='toggle_job_status'),
    
    # Applications
    path('applications/', views.view_applications, name='view_applications'),
    path('applications/<int:job_id>/', views.view_applications, name='view_job_applications'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('candidate/<int:application_id>/', views.candidate_profile, name='candidate_profile'),
    
    # Interviews
    path('interviews/', views.company_interviews, name='company_interviews'),
    path('schedule-interview/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
    path('cancel-interview/<int:interview_id>/', views.cancel_interview, name='cancel_interview'),
    
    # Messages
    path('messages/', views.company_messages, name='company_messages'),
    path('send-message/<int:application_id>/', views.send_message, name='send_message'),
    path('conversation/<int:user_id>/', views.conversation_detail, name='conversation_detail'),
    path('mark-message-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read_company'),
    
    # Analytics
    path('analytics/', views.company_analytics, name='company_analytics'),
    
    # AJAX
    path('dashboard-stats/', views.get_dashboard_stats, name='company_dashboard_stats'),
    
    # Debug
    path('debug-interviews/', views.debug_interviews, name='debug_interviews'),
    
    # ===== SIMPLE STATUS UPDATE - ALWAYS WORKS =====
    path('update-status-simple/<int:application_id>/', views.update_status_simple, name='update_status_simple'),
]