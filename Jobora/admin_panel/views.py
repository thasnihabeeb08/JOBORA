from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from .decorators import admin_required
from datetime import datetime, timedelta
import json
import csv
import os
from collections import defaultdict
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sessions.models import Session
from django.conf import settings

# Import models
from users.models import UserProfile
from jobs.models import Company, Job, Application
from core.models import BlogPost, SuccessStory, Feedback 

# ============================================
# ADMIN LOGIN
# ============================================
def admin_login(request):
    """Admin login page"""
    # If already logged in as admin, go to dashboard
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(request, username=user.username, password=password)
            
            if authenticated_user is not None:
                if authenticated_user.is_superuser or authenticated_user.is_staff:
                    login(request, authenticated_user)
                    
                    # Store login info in session for history
                    request.session['ip_address'] = request.META.get('REMOTE_ADDR', '')
                    request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
                    request.session['login_time'] = timezone.now().isoformat()
                    
                    messages.success(request, f"Welcome back, {authenticated_user.username}!")
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "You don't have admin access")
            else:
                messages.error(request, "Invalid password")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email")
    
    return render(request, 'admin_panel/login.html')


# ============================================
# ADMIN LOGOUT
# ============================================
def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect('admin_login')


# ============================================
# ADMIN DASHBOARD
# ============================================
@admin_required
def admin_dashboard(request):
    """Main admin dashboard with real data"""
    
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get real counts from database
    total_users = UserProfile.objects.count()
    total_companies = Company.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    total_blogs = BlogPost.objects.count()
    total_stories = SuccessStory.objects.count()
    total_feedback = Feedback.objects.count()  # NEW
    unread_feedback = Feedback.objects.filter(is_read=False).count()  # NEW
    
    # Active counts
    active_jobs = Job.objects.filter(is_active=True, is_approved=True).count()
    verified_users = UserProfile.objects.filter(is_verified=True).count()
    verified_companies = Company.objects.filter(is_approved=True).count()
    
    # Pending counts
    pending_companies = Company.objects.filter(is_approved=False).count()
    pending_jobs = Job.objects.filter(is_approved=False).count()
    pending_stories = SuccessStory.objects.filter(status='pending').count()
    
    # New today/week
    new_users_today = UserProfile.objects.filter(created_at__date=today).count()
    new_users_week = UserProfile.objects.filter(created_at__date__gte=week_ago).count()
    applications_today = Application.objects.filter(applied_on__date=today).count()
    
    # Get pending lists
    pending_companies_list = Company.objects.filter(is_approved=False)[:5]
    pending_jobs_list = Job.objects.filter(is_approved=False)[:5]
    
    # Recent applications for activity
    recent_apps = Application.objects.select_related(
        'candidate', 'job', 'job__company'
    ).order_by('-applied_on')[:5]
    
    # Recent feedback for activity (NEW)
    recent_feedback = Feedback.objects.all().order_by('-created_at')[:3]
    
    # Format recent activities
    recent_activities = []
    
    # Add recent applications to activity
    for app in recent_apps:
        # Get candidate name safely
        if app.candidate.first_name or app.candidate.last_name:
            candidate_name = f"{app.candidate.first_name} {app.candidate.last_name}".strip()
        else:
            candidate_name = app.candidate.username
        
        # Calculate time difference
        time_diff = timezone.now() - app.applied_on
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hours ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minutes ago"
        else:
            time_ago = "just now"
        
        recent_activities.append({
            'title': f'New Application for {app.job.title}',
            'description': f'{candidate_name} applied',
            'email': app.candidate.email,
            'time': time_ago,
            'icon': 'fas fa-file-alt',
            'bg_color': '#dbeafe',
            'color': '#2563eb'
        })
    
    # Add recent feedback to activity (NEW)
    for fb in recent_feedback:
        time_diff = timezone.now() - fb.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} days ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hours ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minutes ago"
        else:
            time_ago = "just now"
        
        recent_activities.append({
            'title': f'New Feedback: {fb.subject}',
            'description': f'{fb.name} rated {fb.rating}/5',
            'email': fb.email,
            'time': time_ago,
            'icon': 'fas fa-comment',
            'bg_color': '#fef3c7',
            'color': '#f59e0b'
        })
    
    context = {
        'total_users': total_users,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'total_blogs': total_blogs,
        'total_stories': total_stories,
        'total_feedback': total_feedback,  # NEW
        'unread_feedback': unread_feedback,  # NEW
        'active_jobs': active_jobs,
        'verified_users': verified_users,
        'verified_companies': verified_companies,
        'pending_companies': pending_companies,
        'pending_jobs': pending_jobs,
        'pending_stories': pending_stories,
        'pending_companies_list': pending_companies_list,
        'pending_jobs_list': pending_jobs_list,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'applications_today': applications_today,
        'recent_activities': recent_activities,
        'recent_feedback': recent_feedback,  # NEW
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# ============================================
# USER MANAGEMENT
# ============================================
@admin_required
def admin_users(request):
    """View all users with search and filters"""
    
    # Handle POST request (from search form)
    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        status_filter = request.POST.get('status', '')
        user_type_filter = request.POST.get('type', '')
        
        # Store in session to persist across requests
        request.session['search_query'] = search_query
        request.session['status_filter'] = status_filter
        request.session['user_type_filter'] = user_type_filter
        
        # Redirect to GET to avoid form resubmission
        return redirect(f"{request.path}?page=1")
    
    # Handle GET request (normal page load)
    search_query = request.session.get('search_query', '').strip()
    status_filter = request.session.get('status_filter', '')
    user_type_filter = request.session.get('user_type_filter', '')
    
    # Also check URL parameters (for pagination)
    if request.GET.get('search'):
        search_query = request.GET.get('search', '').strip()
        request.session['search_query'] = search_query
    if request.GET.get('status'):
        status_filter = request.GET.get('status', '')
        request.session['status_filter'] = status_filter
    if request.GET.get('type'):
        user_type_filter = request.GET.get('type', '')
        request.session['user_type_filter'] = user_type_filter
    
    # Start with all users
    users = UserProfile.objects.select_related('user').all().order_by('-created_at')
    
    # Apply search - DIRECT search on User model
    if search_query:
        # Find matching users from auth_user table
        from django.contrib.auth.models import User
        matching_user_ids = []
        for user in User.objects.all():
            if (search_query.lower() in user.username.lower() or
                search_query.lower() in user.first_name.lower() or
                search_query.lower() in user.last_name.lower() or
                search_query.lower() in user.email.lower()):
                matching_user_ids.append(user.id)
        
        if matching_user_ids:
            users = users.filter(user__id__in=matching_user_ids)
        else:
            users = users.none()  # No matches found
    
    # Apply status filter
    if status_filter == 'active':
        users = users.filter(user__is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(user__is_active=False)
    elif status_filter == 'verified':
        users = users.filter(is_verified=True)
    
    # Apply user type filter
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_users = UserProfile.objects.count()
    active_users = UserProfile.objects.filter(user__is_active=True).count()
    verified_users = active_users  # Show active users in verified card
    new_today = UserProfile.objects.filter(created_at__date=timezone.now().date()).count()
    
    context = {
        'users': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'user_type_filter': user_type_filter,
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'new_today': new_today,
    }
    
    return render(request, 'admin_panel/users.html', context)

@admin_required
def admin_user_detail(request, user_id):
    """View single user details"""
    profile = get_object_or_404(UserProfile.objects.select_related('user'), id=user_id)
    
    # Get user's applications
    applications = Application.objects.filter(candidate=profile.user).select_related('job')[:10]
    
    context = {
        'profile': profile,
        'applications': applications,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def block_user(request, user_id):
    """Block a user account"""
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=user_id)
        user = profile.user
        user.is_active = False
        user.save()
        messages.success(request, f"User '{user.username}' has been blocked successfully.")
    return redirect('admin_users')


@admin_required
def unblock_user(request, user_id):
    """Unblock a user account"""
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=user_id)
        user = profile.user
        user.is_active = True
        user.save()
        messages.success(request, f"User '{user.username}' has been unblocked successfully.")
    return redirect('admin_users')


@admin_required
def delete_user(request, user_id):
    """Delete a user account"""
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=user_id)
        username = profile.user.username
        profile.user.delete()
        messages.success(request, f"User '{username}' has been deleted permanently.")
    return redirect('admin_users')


# ============================================
# COMPANY MANAGEMENT
# ============================================
@admin_required
def admin_companies(request):
    """View all companies with search and filters"""
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    industry_filter = request.GET.get('industry', '')
    
    # Get all companies
    companies = Company.objects.all().order_by('-created_at')
    
    # FIXED: Apply search filter - NOW INCLUDES EMAIL!
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |  # ← EMAIL SEARCH FIXED
            Q(contact_person__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'approved':
        companies = companies.filter(is_approved=True)
    elif status_filter == 'pending':
        companies = companies.filter(is_approved=False)
    
    # Apply industry filter
    if industry_filter:
        companies = companies.filter(industry=industry_filter)
    
    # Pagination
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get counts for stats
    total_companies = Company.objects.count()
    approved_companies = Company.objects.filter(is_approved=True).count()
    pending_companies = Company.objects.filter(is_approved=False).count()
    
    # Get unique industries for filter dropdown
    industries = Company.objects.values_list('industry', flat=True).distinct()
    industry_choices = []
    for ind in industries:
        if ind:
            display_value = dict(Company.INDUSTRY_CHOICES).get(ind, ind)
            industry_choices.append((ind, display_value))
    
    context = {
        'companies': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'industry_filter': industry_filter,
        'total_companies': total_companies,
        'approved_companies': approved_companies,
        'pending_companies': pending_companies,
        'industry_choices': industry_choices,
    }
    
    return render(request, 'admin_panel/companies.html', context)

@admin_required
def admin_company_detail(request, company_id):
    """View single company details"""
    company = get_object_or_404(Company, id=company_id)
    
    # Get jobs posted by this company
    jobs = Job.objects.filter(company=company).order_by('-posted_on')
    
    context = {
        'company': company,
        'jobs': jobs,
    }
    return render(request, 'admin_panel/company_detail.html', context)


@admin_required
def verify_company(request, company_id):
    """Verify a company"""
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        company.is_approved = True
        company.save()
        messages.success(request, f"Company '{company.name}' has been verified successfully.")
    return redirect('admin_companies')


@admin_required
def reject_company(request, company_id):
    """Reject a company"""
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        company.is_approved = False
        company.save()
        messages.success(request, f"Company '{company.name}' has been rejected.")
    return redirect('admin_companies')


@admin_required
def delete_company(request, company_id):
    """Delete a company"""
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        company_name = company.name
        company.delete()
        messages.success(request, f"Company '{company_name}' has been deleted permanently.")
    return redirect('admin_companies')


# ============================================
# JOB MANAGEMENT
# ============================================
@admin_required
def admin_jobs(request):
    """View all jobs with search and filters"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    company_filter = request.GET.get('company', '')
    job_type_filter = request.GET.get('job_type', '')
    
    # Get all jobs
    jobs = Job.objects.all().select_related('company').order_by('-posted_on')
    
    # Apply search filter
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'active':
        jobs = jobs.filter(is_active=True, is_approved=True)
    elif status_filter == 'inactive':
        jobs = jobs.filter(is_active=False)
    elif status_filter == 'pending':
        jobs = jobs.filter(is_approved=False)
    elif status_filter == 'expired':
        jobs = jobs.filter(application_deadline__lt=timezone.now().date())
    
    # Apply company filter
    if company_filter:
        jobs = jobs.filter(company_id=company_filter)
    
    # Apply job type filter
    if job_type_filter:
        jobs = jobs.filter(job_type=job_type_filter)
    
    # Pagination - Show 20 jobs per page
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Calculate starting serial number for current page
    start_index = (page_obj.number - 1) * 20
    
    # Get counts for stats
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True, is_approved=True).count()
    pending_jobs = Job.objects.filter(is_approved=False).count()
    expired_jobs = Job.objects.filter(application_deadline__lt=timezone.now().date()).count()
    
    # Get all companies for filter dropdown
    companies = Company.objects.all().order_by('name')
    
    # Job type choices for filter
    job_type_choices = Job.JOB_TYPE_CHOICES
    
    context = {
        'jobs': page_obj,
        'start_index': start_index,  # Add this for sequential numbering
        'search_query': search_query,
        'status_filter': status_filter,
        'company_filter': company_filter,
        'job_type_filter': job_type_filter,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'pending_jobs': pending_jobs,
        'expired_jobs': expired_jobs,
        'companies': companies,
        'job_type_choices': job_type_choices,
    }
    
    return render(request, 'admin_panel/jobs.html', context)


@admin_required
def admin_job_detail(request, job_id):
    """View single job details"""
    job = get_object_or_404(Job.objects.select_related('company'), id=job_id)
    
    # Get applications for this job
    applications = Application.objects.filter(job=job).select_related('candidate')[:20]
    
    context = {
        'job': job,
        'applications': applications,
    }
    return render(request, 'admin_panel/job_detail.html', context)


@admin_required
def approve_job(request, job_id):
    """Approve a job posting"""
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id)
        job.is_approved = True
        job.is_active = True
        job.save()
        messages.success(request, f"Job '{job.title}' has been approved successfully.")
    return redirect('admin_jobs')


@admin_required
def reject_job(request, job_id):
    """Reject a job posting"""
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id)
        job.is_approved = False
        job.is_active = False
        job.save()
        messages.success(request, f"Job '{job.title}' has been rejected.")
    return redirect('admin_jobs')


@admin_required
def delete_job(request, job_id):
    """Delete a job posting"""
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id)
        job_title = job.title
        job.delete()
        messages.success(request, f"Job '{job_title}' has been deleted permanently.")
    return redirect('admin_jobs')


# ============================================
# APPLICATION MANAGEMENT
# ============================================
@admin_required
def admin_applications(request):
    """View all applications with search and filters"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    job_filter = request.GET.get('job', '')
    company_filter = request.GET.get('company', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get all applications
    applications = Application.objects.all().select_related(
        'job', 'candidate', 'job__company'
    ).order_by('-applied_on')
    
    # Apply search filter (candidate name, email, job title)
    if search_query:
        applications = applications.filter(
            Q(candidate__first_name__icontains=search_query) |
            Q(candidate__last_name__icontains=search_query) |
            Q(candidate__email__icontains=search_query) |
            Q(candidate__username__icontains=search_query) |
            Q(job__title__icontains=search_query) |
            Q(job__company__name__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Apply job filter
    if job_filter:
        applications = applications.filter(job_id=job_filter)
    
    # Apply company filter
    if company_filter:
        applications = applications.filter(job__company_id=company_filter)
    
    # Apply date range filter
    if date_from:
        applications = applications.filter(applied_on__date__gte=date_from)
    if date_to:
        applications = applications.filter(applied_on__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get counts for stats
    total_applications = Application.objects.count()
    applied_count = Application.objects.filter(status='applied').count()
    shortlisted_count = Application.objects.filter(status='shortlisted').count()
    interview_count = Application.objects.filter(status='interview').count()
    selected_count = Application.objects.filter(status='selected').count()
    rejected_count = Application.objects.filter(status='rejected').count()
    
    # Get today's applications
    today = timezone.now().date()
    today_applications = Application.objects.filter(applied_on__date=today).count()
    
    # Get all jobs and companies for filter dropdowns
    jobs = Job.objects.all().order_by('title')
    companies = Company.objects.all().order_by('name')
    
    # Status choices for filter
    status_choices = Application.STATUS_CHOICES
    
    context = {
        'applications': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'job_filter': job_filter,
        'company_filter': company_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_applications': total_applications,
        'applied_count': applied_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'today_applications': today_applications,
        'jobs': jobs,
        'companies': companies,
        'status_choices': status_choices,
    }
    
    return render(request, 'admin_panel/applications.html', context)


@admin_required
def admin_application_detail(request, application_id):
    """View single application details"""
    application = get_object_or_404(
        Application.objects.select_related(
            'job', 'candidate', 'job__company'
        ), 
        id=application_id
    )
    
    # Get candidate profile
    try:
        profile = UserProfile.objects.get(user=application.candidate)
    except UserProfile.DoesNotExist:
        profile = None
    
    context = {
        'application': application,
        'profile': profile,
    }
    
    return render(request, 'admin_panel/application_detail.html', context)


@admin_required
def update_application_status(request, application_id):
    """Update application status"""
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Application.STATUS_CHOICES).keys():
            application.status = new_status
            application.save()
            messages.success(request, f"Application status updated to {application.get_status_display()}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect('admin_application_detail', application_id=application_id)


@admin_required
def export_applications(request):
    """Export applications as CSV"""
    
    # Create HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Application ID', 'Candidate Name', 'Candidate Email', 'Job Title', 
        'Company', 'Applied Date', 'Status', 'Expected Salary', 'Cover Letter'
    ])
    
    # Get all applications (with filters if any)
    applications = Application.objects.all().select_related(
        'job', 'candidate', 'job__company'
    ).order_by('-applied_on')
    
    # Apply filters from GET parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    job_filter = request.GET.get('job', '')
    company_filter = request.GET.get('company', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        applications = applications.filter(
            Q(candidate__first_name__icontains=search_query) |
            Q(candidate__last_name__icontains=search_query) |
            Q(candidate__email__icontains=search_query) |
            Q(job__title__icontains=search_query) |
            Q(job__company__name__icontains=search_query)
        )
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if job_filter:
        applications = applications.filter(job_id=job_filter)
    
    if company_filter:
        applications = applications.filter(job__company_id=company_filter)
    
    if date_from:
        applications = applications.filter(applied_on__date__gte=date_from)
    
    if date_to:
        applications = applications.filter(applied_on__date__lte=date_to)
    
    # Write data rows
    for app in applications:
        writer.writerow([
            app.id,
            app.candidate.get_full_name() or app.candidate.username,
            app.candidate.email,
            app.job.title,
            app.job.company.name,
            app.applied_on.strftime('%Y-%m-%d'),
            app.get_status_display(),
            app.expected_salary or '',
            app.cover_letter[:100] + '...' if app.cover_letter else ''
        ])
    
    return response


@admin_required
def admin_analytics(request):
    """Analytics dashboard with charts and reports"""
    
    # Get date range from request (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # ============================================
    # USER TYPE DISTRIBUTION
    # ============================================
    user_types_raw = UserProfile.objects.values('user_type').annotate(count=Count('id')).order_by('-count')
    user_type_distribution = []
    total_users = UserProfile.objects.count()
    
    for ut in user_types_raw:
        if ut['user_type']:
            if ut['user_type'] == 'experienced':
                type_name = 'Experienced'
            elif ut['user_type'] == 'fresher':
                type_name = 'Fresher'
            else:
                type_name = ut['user_type'].title()
            
            percentage = round((ut['count'] / total_users * 100), 1) if total_users > 0 else 0
            user_type_distribution.append({
                'name': type_name,
                'count': ut['count'],
                'percentage': percentage
            })
    
    # ============================================
    # JOB TYPE DISTRIBUTION
    # ============================================
    job_types_raw = Job.objects.values('job_type').annotate(count=Count('id')).order_by('-count')
    job_type_distribution = []
    total_jobs = Job.objects.count()
    
    for jt in job_types_raw:
        if jt['job_type']:
            if jt['job_type'] == 'full_time':
                type_name = 'Full Time'
            elif jt['job_type'] == 'part_time':
                type_name = 'Part Time'
            elif jt['job_type'] == 'internship':
                type_name = 'Internship'
            elif jt['job_type'] == 'freelance':
                type_name = 'Freelance'
            else:
                type_name = jt['job_type'].title()
            
            percentage = round((jt['count'] / total_jobs * 100), 1) if total_jobs > 0 else 0
            job_type_distribution.append({
                'name': type_name,
                'count': jt['count'],
                'percentage': percentage
            })
    
    # ============================================
    # INDUSTRY DISTRIBUTION
    # ============================================
    industries_raw = Company.objects.values('industry').annotate(count=Count('id')).order_by('-count')
    industry_distribution = []
    total_companies = Company.objects.count()
    
    industry_display = {
        'it': 'IT Services',
        'finance': 'Finance',
        'healthcare': 'Healthcare',
        'education': 'Education',
        'manufacturing': 'Manufacturing',
        'retail': 'Retail',
        'hospitality': 'Hospitality',
    }
    
    for ind in industries_raw:
        if ind['industry']:
            industry_name = industry_display.get(ind['industry'], ind['industry'].title())
            percentage = round((ind['count'] / total_companies * 100), 1) if total_companies > 0 else 0
            industry_distribution.append({
                'name': industry_name,
                'count': ind['count'],
                'percentage': percentage
            })
    
    # ============================================
    # APPLICATION FUNNEL DATA
    # ============================================
    funnel_data = {
        'applied': Application.objects.filter(status='applied').count(),
        'shortlisted': Application.objects.filter(status='shortlisted').count(),
        'interview': Application.objects.filter(status='interview').count(),
        'selected': Application.objects.filter(status='selected').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    
    total_apps = funnel_data['applied']
    shortlist_rate = round((funnel_data['shortlisted'] / total_apps * 100), 1) if total_apps > 0 else 0
    interview_rate = round((funnel_data['interview'] / total_apps * 100), 1) if total_apps > 0 else 0
    selection_rate = round((funnel_data['selected'] / total_apps * 100), 1) if total_apps > 0 else 0
    rejection_rate = round((funnel_data['rejected'] / total_apps * 100), 1) if total_apps > 0 else 0
    
    # ============================================
    # TOP PERFORMERS
    # ============================================
    top_companies = Company.objects.annotate(
        job_count=Count('jobs')
    ).order_by('-job_count')[:10]
    
    top_jobs = Job.objects.annotate(
        app_count=Count('applications')
    ).order_by('-app_count')[:10]
    
    # ============================================
    # RECENT APPLICATIONS
    # ============================================
    recent_applications = Application.objects.select_related(
        'candidate', 'job', 'job__company'
    ).order_by('-applied_on')[:10]
    
    # ============================================
    # TOTALS
    # ============================================
    total_users = UserProfile.objects.count()
    total_companies = Company.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    
    verified_users = UserProfile.objects.filter(is_verified=True).count()
    verified_companies = Company.objects.filter(is_approved=True).count()
    active_jobs = Job.objects.filter(is_active=True, is_approved=True).count()
    pending_applications = Application.objects.filter(status='applied').count()
    
    # ============================================
    # CHART DATA
    # ============================================
    user_daily = []
    job_daily = []
    
    current = start_date
    while current <= end_date:
        user_daily.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': UserProfile.objects.filter(created_at__date=current).count()
        })
        job_daily.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': Job.objects.filter(posted_on__date=current).count()
        })
        current += timedelta(days=1)
    
    context = {
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        
        # Distributions
        'user_type_distribution': user_type_distribution,
        'job_type_distribution': job_type_distribution,
        'industry_distribution': industry_distribution,
        
        # Funnel data
        'funnel_data': funnel_data,
        'shortlist_rate': shortlist_rate,
        'interview_rate': interview_rate,
        'selection_rate': selection_rate,
        'rejection_rate': rejection_rate,
        
        # Top performers
        'top_companies': top_companies,
        'top_jobs': top_jobs,
        
        # Recent activity
        'recent_applications': recent_applications,
        
        # Totals
        'total_users': total_users,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'verified_users': verified_users,
        'verified_companies': verified_companies,
        'active_jobs': active_jobs,
        'pending_applications': pending_applications,
        
        # Chart data
        'user_daily': json.dumps(user_daily),
        'job_daily': json.dumps(job_daily),
    }
    
    return render(request, 'admin_panel/analytics.html', context)

@admin_required
def analytics_data(request):
    """AJAX endpoint to get analytics data for charts"""
    
    # Get date range
    days = int(request.GET.get('days', 30))
    chart_type = request.GET.get('chart', 'users')
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    data = {}
    
    if chart_type == 'users':
        # User growth data
        labels = []
        values = []
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %d'))
            count = UserProfile.objects.filter(created_at__date=current).count()
            values.append(count)
            current += timedelta(days=1)
        
        data = {
            'labels': labels,
            'values': values,
            'title': 'User Registration Trend'
        }
    
    elif chart_type == 'jobs':
        # Jobs posted data
        labels = []
        values = []
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %d'))
            count = Job.objects.filter(posted_on__date=current).count()
            values.append(count)
            current += timedelta(days=1)
        
        data = {
            'labels': labels,
            'values': values,
            'title': 'Jobs Posted Trend'
        }
    
    elif chart_type == 'applications':
        # Applications data
        labels = []
        values = []
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%b %d'))
            count = Application.objects.filter(applied_on__date=current).count()
            values.append(count)
            current += timedelta(days=1)
        
        data = {
            'labels': labels,
            'values': values,
            'title': 'Applications Received Trend'
        }
    
    elif chart_type == 'user_types':
        # User type distribution
        user_types = UserProfile.objects.values('user_type').annotate(count=Count('id'))
        labels = []
        values = []
        for ut in user_types:
            if ut['user_type']:
                labels.append(dict(UserProfile.USER_TYPES).get(ut['user_type'], ut['user_type']))
                values.append(ut['count'])
        
        data = {
            'labels': labels,
            'values': values,
            'title': 'User Type Distribution'
        }
    
    elif chart_type == 'funnel':
        # Application funnel
        funnel = {
            'Applied': Application.objects.filter(status='applied').count(),
            'Shortlisted': Application.objects.filter(status='shortlisted').count(),
            'Interview': Application.objects.filter(status='interview').count(),
            'Selected': Application.objects.filter(status='selected').count(),
            'Rejected': Application.objects.filter(status='rejected').count(),
        }
        data = {
            'labels': list(funnel.keys()),
            'values': list(funnel.values()),
            'title': 'Application Funnel'
        }
    
    return JsonResponse(data)


@admin_required
def export_analytics_pdf(request):
    """Export analytics report as CSV (same as Excel export)"""
    return export_analytics_excel(request)

@admin_required
def export_analytics_excel(request):
    """Export analytics report as CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    from django.db.models import Count
    
    # Create HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['JOBORA ANALYTICS REPORT'])
    writer.writerow(['Generated on:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # ============================================
    # SUMMARY STATS
    # ============================================
    writer.writerow(['SUMMARY STATISTICS'])
    writer.writerow(['Metric', 'Value'])
    
    total_users = UserProfile.objects.count()
    total_companies = Company.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    
    writer.writerow(['Total Users', total_users])
    writer.writerow(['Verified Users', UserProfile.objects.filter(is_verified=True).count()])
    writer.writerow(['Total Companies', total_companies])
    writer.writerow(['Verified Companies', Company.objects.filter(is_approved=True).count()])
    writer.writerow(['Total Jobs', total_jobs])
    writer.writerow(['Active Jobs', Job.objects.filter(is_active=True, is_approved=True).count()])
    writer.writerow(['Total Applications', total_applications])
    writer.writerow([])
    
    # ============================================
    # USER TYPE DISTRIBUTION
    # ============================================
    writer.writerow(['USER TYPE DISTRIBUTION'])
    writer.writerow(['User Type', 'Count', 'Percentage'])
    
    user_types = UserProfile.objects.values('user_type').annotate(count=Count('id'))
    for ut in user_types:
        if ut['user_type']:
            type_name = 'Experienced' if ut['user_type'] == 'experienced' else 'Fresher'
            percentage = round((ut['count'] / total_users * 100), 1) if total_users > 0 else 0
            writer.writerow([type_name, ut['count'], f"{percentage}%"])
    writer.writerow([])
    
    # ============================================
    # JOB TYPE DISTRIBUTION
    # ============================================
    writer.writerow(['JOB TYPE DISTRIBUTION'])
    writer.writerow(['Job Type', 'Count', 'Percentage'])
    
    job_types = Job.objects.values('job_type').annotate(count=Count('id'))
    for jt in job_types:
        if jt['job_type']:
            type_name = {
                'full_time': 'Full Time',
                'part_time': 'Part Time',
                'internship': 'Internship',
                'freelance': 'Freelance'
            }.get(jt['job_type'], jt['job_type'])
            percentage = round((jt['count'] / total_jobs * 100), 1) if total_jobs > 0 else 0
            writer.writerow([type_name, jt['count'], f"{percentage}%"])
    writer.writerow([])
    
    # ============================================
    # INDUSTRY DISTRIBUTION
    # ============================================
    writer.writerow(['INDUSTRY DISTRIBUTION'])
    writer.writerow(['Industry', 'Companies', 'Percentage'])
    
    industries = Company.objects.values('industry').annotate(count=Count('id'))
    industry_display = {
        'it': 'IT Services',
        'finance': 'Finance',
        'healthcare': 'Healthcare',
        'education': 'Education',
        'manufacturing': 'Manufacturing',
        'retail': 'Retail',
        'hospitality': 'Hospitality',
    }
    
    for ind in industries:
        if ind['industry']:
            industry_name = industry_display.get(ind['industry'], ind['industry'].title())
            percentage = round((ind['count'] / total_companies * 100), 1) if total_companies > 0 else 0
            writer.writerow([industry_name, ind['count'], f"{percentage}%"])
    writer.writerow([])
    
    # ============================================
    # APPLICATION STATUS
    # ============================================
    writer.writerow(['APPLICATION STATUS'])
    writer.writerow(['Status', 'Count', 'Percentage'])
    
    funnel_data = {
        'applied': Application.objects.filter(status='applied').count(),
        'shortlisted': Application.objects.filter(status='shortlisted').count(),
        'interview': Application.objects.filter(status='interview').count(),
        'selected': Application.objects.filter(status='selected').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    
    writer.writerow(['Applied', funnel_data['applied'], '100%'])
    if total_applications > 0:
        shortlist_rate = round((funnel_data['shortlisted'] / total_applications * 100), 1)
        interview_rate = round((funnel_data['interview'] / total_applications * 100), 1)
        selection_rate = round((funnel_data['selected'] / total_applications * 100), 1)
        rejection_rate = round((funnel_data['rejected'] / total_applications * 100), 1)
    else:
        shortlist_rate = interview_rate = selection_rate = rejection_rate = 0
    
    writer.writerow(['Shortlisted', funnel_data['shortlisted'], f"{shortlist_rate}%"])
    writer.writerow(['Interview', funnel_data['interview'], f"{interview_rate}%"])
    writer.writerow(['Selected', funnel_data['selected'], f"{selection_rate}%"])
    writer.writerow(['Rejected', funnel_data['rejected'], f"{rejection_rate}%"])
    writer.writerow([])
    
    # ============================================
    # TOP COMPANIES
    # ============================================
    writer.writerow(['TOP COMPANIES BY JOBS POSTED'])
    writer.writerow(['Company', 'Industry', 'Jobs Posted'])
    
    top_companies = Company.objects.annotate(job_count=Count('jobs')).order_by('-job_count')[:10]
    for company in top_companies:
        writer.writerow([company.name, company.get_industry_display() or '—', company.job_count])
    writer.writerow([])
    
    # ============================================
    # TOP JOBS
    # ============================================
    writer.writerow(['MOST APPLIED JOBS'])
    writer.writerow(['Job Title', 'Company', 'Applications'])
    
    top_jobs = Job.objects.annotate(app_count=Count('applications')).order_by('-app_count')[:10]
    for job in top_jobs:
        writer.writerow([job.title, job.company.name, job.app_count])
    
    return response


# ============================================
# ADMIN PROFILE & SETTINGS
# ============================================
@admin_required
def admin_profile(request):
    """Admin profile settings"""
    if request.method == 'POST':
        # Update basic info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('admin_profile')
    
    return render(request, 'admin_panel/profile.html', {
        'user': request.user
    })


@admin_required
def admin_change_password(request):
    """Change admin password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('admin_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'admin_panel/change_password.html', {
        'form': form
    })


@admin_required
def admin_login_history(request):
    """View login history"""
    login_history = []
    
    # Get all sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for session in sessions:
        try:
            data = session.get_decoded()
            if str(data.get('_auth_user_id')) == str(request.user.id):
                login_history.append({
                    'ip': data.get('ip_address', 'Unknown'),
                    'user_agent': data.get('user_agent', 'Unknown')[:50] + '...',
                    'login_time': session.expire_date - timezone.timedelta(days=14),
                })
        except:
            continue
    
    return render(request, 'admin_panel/login_history.html', {
        'login_history': login_history[:10]
    })


# ============================================
# CONTENT MANAGEMENT - BLOG POSTS
# ============================================
from django import forms

# Blog Post Form
class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'category', 'content', 'excerpt', 'image_url', 'is_published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


@admin_required
def admin_blog_list(request):
    """List all blog posts"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    posts = BlogPost.objects.all().order_by('-date_posted')
    
    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    
    if category_filter:
        posts = posts.filter(category=category_filter)
    
    if status_filter == 'published':
        posts = posts.filter(is_published=True)
    elif status_filter == 'draft':
        posts = posts.filter(is_published=False)
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': BlogPost.CATEGORY_CHOICES,
        'total_posts': BlogPost.objects.count(),
        'published_posts': BlogPost.objects.filter(is_published=True).count(),
        'draft_posts': BlogPost.objects.filter(is_published=False).count(),
    }
    return render(request, 'admin_panel/content/blog_list.html', context)


@admin_required
def admin_blog_create(request):
    """Create new blog post"""
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'Blog post "{post.title}" created successfully!')
            return redirect('admin_blog_list')
    else:
        form = BlogPostForm()
    
    return render(request, 'admin_panel/content/blog_form.html', {
        'form': form,
        'title': 'Create Blog Post'
    })


@admin_required
def admin_blog_detail(request, post_id):
    """View blog post details"""
    post = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'admin_panel/content/blog_detail.html', {'post': post})


# Edit function removed as requested


@admin_required
def admin_blog_delete(request, post_id):
    """Delete blog post"""
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        title = post.title
        post.delete()
        messages.success(request, f'Blog post "{title}" deleted successfully!')
    return redirect('admin_blog_list')


@admin_required
def admin_blog_toggle_publish(request, post_id):
    """Toggle publish status"""
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, id=post_id)
        post.is_published = not post.is_published
        post.save()
        status = 'published' if post.is_published else 'unpublished'
        messages.success(request, f'Blog post "{post.title}" {status} successfully!')
    return redirect('admin_blog_list')


# ============================================
# CONTENT MANAGEMENT - SUCCESS STORIES
# ============================================
@admin_required
def admin_stories_list(request):
    """List all success stories"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    stories = SuccessStory.objects.all().order_by('-created_at')
    
    if search_query:
        stories = stories.filter(
            Q(full_name__icontains=search_query) | 
            Q(current_role__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if status_filter:
        stories = stories.filter(status=status_filter)
    
    paginator = Paginator(stories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'stories': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_stories': SuccessStory.objects.count(),
        'pending_stories': SuccessStory.objects.filter(status='pending').count(),
        'approved_stories': SuccessStory.objects.filter(status='approved').count(),
        'rejected_stories': SuccessStory.objects.filter(status='rejected').count(),
    }
    return render(request, 'admin_panel/content/stories_list.html', context)


@admin_required
def admin_story_detail(request, story_id):
    """View success story details"""
    story = get_object_or_404(SuccessStory, id=story_id)
    return render(request, 'admin_panel/content/story_detail.html', {'story': story})


@admin_required
def admin_story_approve(request, story_id):
    """Approve success story"""
    if request.method == 'POST':
        story = get_object_or_404(SuccessStory, id=story_id)
        story.status = 'approved'
        story.approved_by = request.user
        story.save()
        messages.success(request, f'Success story from {story.full_name} approved and published!')
    return redirect('admin_stories_list')


@admin_required
def admin_story_reject(request, story_id):
    """Reject success story"""
    if request.method == 'POST':
        story = get_object_or_404(SuccessStory, id=story_id)
        story.status = 'rejected'
        story.save()
        messages.success(request, f'Success story from {story.full_name} rejected.')
    return redirect('admin_stories_list')


@admin_required
def admin_story_delete(request, story_id):
    """Delete success story"""
    if request.method == 'POST':
        story = get_object_or_404(SuccessStory, id=story_id)
        name = story.full_name
        story.delete()
        messages.success(request, f'Success story from {name} deleted permanently.')
    return redirect('admin_stories_list')

@admin_required
def admin_feedback(request):
    """View all feedback submissions"""
    from django.core.paginator import Paginator
    
    # Get all feedback, newest first
    feedback_list = Feedback.objects.all().order_by('-created_at')
    
    # Get counts
    total = feedback_list.count()
    unread = feedback_list.filter(is_read=False).count()
    
    # Pagination
    paginator = Paginator(feedback_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'feedbacks': page_obj,
        'total': total,
        'unread': unread,
    }
    return render(request, 'admin_panel/feedback.html', context)


@admin_required
def mark_feedback_read(request, feedback_id):
    """Mark feedback as read"""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.is_read = True
    feedback.save()
    messages.success(request, 'Feedback marked as read.')
    return redirect('admin_feedback')


@admin_required
def delete_feedback(request, feedback_id):
    """Delete feedback"""
    if request.method == 'POST':
        feedback = get_object_or_404(Feedback, id=feedback_id)
        feedback.delete()
        messages.success(request, 'Feedback deleted successfully.')
    return redirect('admin_feedback')
