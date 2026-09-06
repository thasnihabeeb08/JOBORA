from django.urls import path
from . import views

urlpatterns = [
    # Admin Login
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/block/', views.block_user, name='block_user'),
    path('users/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Company Management
    path('companies/', views.admin_companies, name='admin_companies'),
    path('companies/<int:company_id>/', views.admin_company_detail, name='admin_company_detail'),
    path('companies/<int:company_id>/verify/', views.verify_company, name='verify_company'),
    path('companies/<int:company_id>/reject/', views.reject_company, name='reject_company'),
    path('companies/<int:company_id>/delete/', views.delete_company, name='delete_company'),
    
    # Job Management
    path('jobs/', views.admin_jobs, name='admin_jobs'),
    path('jobs/<int:job_id>/', views.admin_job_detail, name='admin_job_detail'),
    path('jobs/<int:job_id>/approve/', views.approve_job, name='approve_job'),
    path('jobs/<int:job_id>/reject/', views.reject_job, name='reject_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    # Application Management
    path('applications/', views.admin_applications, name='admin_applications'),
    path('applications/<int:application_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('applications/export/', views.export_applications, name='export_applications'),
    
    # Analytics & Reports
    path('analytics/', views.admin_analytics, name='admin_analytics'),
    path('analytics/data/', views.analytics_data, name='analytics_data'),
    path('analytics/export/pdf/', views.export_analytics_pdf, name='export_analytics_pdf'),
    path('analytics/export/excel/', views.export_analytics_excel, name='export_analytics_excel'),
    
    # Admin Profile & Settings
    path('profile/', views.admin_profile, name='admin_profile'),
    path('profile/change-password/', views.admin_change_password, name='admin_change_password'),
    path('profile/login-history/', views.admin_login_history, name='admin_login_history'),
    
    # ===== CONTENT MANAGEMENT =====
    # Blog Posts
    path('content/blog/', views.admin_blog_list, name='admin_blog_list'),
    path('content/blog/create/', views.admin_blog_create, name='admin_blog_create'),
    path('content/blog/<int:post_id>/', views.admin_blog_detail, name='admin_blog_detail'),
    path('content/blog/<int:post_id>/delete/', views.admin_blog_delete, name='admin_blog_delete'),
    path('content/blog/<int:post_id>/toggle-publish/', views.admin_blog_toggle_publish, name='admin_blog_toggle_publish'),
    
    # Success Stories
    path('content/stories/', views.admin_stories_list, name='admin_stories_list'),
    path('content/stories/<int:story_id>/', views.admin_story_detail, name='admin_story_detail'),
    path('content/stories/<int:story_id>/approve/', views.admin_story_approve, name='admin_story_approve'),
    path('content/stories/<int:story_id>/reject/', views.admin_story_reject, name='admin_story_reject'),
    path('content/stories/<int:story_id>/delete/', views.admin_story_delete, name='admin_story_delete'),
    
    # ===== FEEDBACK MANAGEMENT (ADD THESE 3 LINES) =====
    path('feedback/', views.admin_feedback, name='admin_feedback'),
    path('feedback/<int:feedback_id>/mark-read/', views.mark_feedback_read, name='mark_feedback_read'),
    path('feedback/<int:feedback_id>/delete/', views.delete_feedback, name='delete_feedback'),
    
    # Root redirect
    path('', views.admin_login, name='admin_login_root'),
]