from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Profile
    path('dashboard/', views.job_seeker_dashboard, name='job_seeker_dashboard'),
    path('edit-profile/', views.edit_job_seeker_profile, name='edit_job_seeker_profile'),  # FIXED
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
    
    # Job Search & Applications
    path('search/', views.search_jobs, name='search_jobs'),
    path('job/<int:job_id>/', views.view_job_detail, name='view_job_detail'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/quick-apply/', views.quick_apply, name='quick_apply'),
    path('company/<int:company_id>/', views.view_company_profile, name='view_company_profile'),
    
    # My Applications
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Interviews
    path('my-interviews/', views.my_interviews, name='my_interviews'),
    path('interview/<int:interview_id>/', views.interview_detail, name='interview_detail'),
    path('interview/<int:interview_id>/cancel/', views.cancel_interview, name='cancel_interview'),
    
    # Messages
    path('my-messages/', views.my_messages, name='my_messages'),
    path('send-message/', views.send_message, name='send_message'),
    path('start-conversation/', views.start_conversation, name='start_conversation'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('conversation/<int:conversation_id>/', views.get_conversation, name='get_conversation'),
    path('message-updates/', views.message_updates, name='message_updates'),
    
    # Delete URLs
    path('delete-message/', views.delete_message, name='delete_message'),
    path('delete-conversation/', views.delete_conversation, name='delete_conversation'),
    
    # Saved Jobs
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    path('save-job/<int:job_id>/', views.save_job, name='save_job'),
    path('saved-jobs-count/', views.saved_jobs_count, name='saved_jobs_count'),
    
    # Analytics & Tools
    path('analytics/', views.job_seeker_analytics, name='job_seeker_analytics'),
    path('download-resume/', views.download_resume, name='download_resume'),
    path('subscribe-alerts/', views.subscribe_job_alerts, name='subscribe_job_alerts'),
    
    # Account Management
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # AJAX & Live Updates
    path('test-ajax/', views.test_ajax, name='test_ajax'),
    path('dashboard-stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
]