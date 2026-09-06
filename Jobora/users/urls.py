from django.urls import path
from . import views

urlpatterns = [
    # ========== AUTHENTICATION URLS ==========
    
    # Registration URLs
    path('register/company/', views.register_company, name='register_company'),
    path('register/job-seeker/', views.register_job_seeker, name='register_job_seeker'),
    path('register/', views.register_company, name='register'),  # Default to company register
    
    # Login URLs
    path('login/', views.user_login, name='login'),  # Universal login
    path('login/job-seeker/', views.login_job_seeker, name='login_job_seeker'),  # Job seeker specific login
    path('login/company/', views.login_company, name='login_company'),  # ✅ ADD THIS LINE - Company specific login
    
    # Logout URL
    path('logout/', views.user_logout, name='logout'),
    
    # ========== PASSWORD RESET URLS ==========
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # ========== DASHBOARD URLS ==========
    path('company/dashboard/', views.company_dashboard, name='company_dashboard'),
    path('job-seeker/dashboard/', views.job_seeker_dashboard, name='job_seeker_dashboard'),
    
    # ========== PROFILE MANAGEMENT URLS ==========
    path('profile/create/', views.create_profile, name='create_profile'),
    
    # ========== SEARCH URLS ==========
    path('search-jobs/', views.search_jobs, name='search_jobs'),
]