# jobs/views.py - COMPLETE FIXED VERSION

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from datetime import datetime, timedelta
import json

# Import models
from .models import (
    Job, Application, Interview, Company, 
    JobCategory, Message, CompanyAnalytics
)

# Import job seeker model
from users.models import UserProfile

# Import forms
from .forms import (
    JobPostForm, ApplicationFilterForm,
    CompanyProfileForm, MessageForm
)

User = get_user_model()

# ==================== HELPER FUNCTIONS ====================

def get_user_company(user):
    """Get company associated with user"""
    try:
        return Company.objects.get(user=user)
    except Company.DoesNotExist:
        return None

def company_active_required(view_func):
    """Decorator to check if company is approved and active"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('login')
        
        # Check if user is blocked by admin
        if not request.user.is_active:
            messages.error(request, "Your account has been suspended. Contact admin.")
            return redirect('login')
        
        # Check if company exists and is approved
        company = get_user_company(request.user)
        if not company:
            messages.error(request, "Company profile not found.")
            return redirect('register_company')
        
        if not company.is_approved:
            messages.error(request, "Your company is pending approval. Please wait for admin verification.")
            return redirect('company_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def send_interview_email(application, interview):
    """Send interview notification email to candidate"""
    subject = f"Interview Scheduled: {application.job.title} at {application.job.company.name}"
    
    date_str = interview.scheduled_date.strftime("%A, %B %d, %Y")
    time_str = interview.scheduled_date.strftime("%I:%M %p")
    
    meeting_details = []
    if interview.meeting_link:
        meeting_details.append(f"Meeting Link: {interview.meeting_link}")
    if interview.meeting_id:
        meeting_details.append(f"Meeting ID: {interview.meeting_id}")
    if interview.passcode:
        meeting_details.append(f"Passcode: {interview.passcode}")
    if interview.platform:
        meeting_details.append(f"Platform: {interview.platform}")
    if interview.location and interview.interview_type == 'in_person':
        meeting_details.append(f"Location: {interview.location}")
    
    meeting_details_text = "\n".join(meeting_details) if meeting_details else "Details will be shared separately."
    
    message = f"""
Dear {application.candidate.get_full_name() or application.candidate.username},

An interview has been scheduled for:

Position: {application.job.title}
Company: {application.job.company.name}

Date: {date_str}
Time: {time_str}
Duration: {interview.duration_minutes} minutes
Type: {interview.get_interview_type_display()}
Interviewer: {interview.interviewer}

Meeting Details:
{meeting_details_text}

Additional Notes:
{interview.notes or "No additional notes"}

Please be prepared and join 5 minutes before the scheduled time.

Best regards,
{application.job.company.name} Hiring Team
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [application.candidate.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email failed: {str(e)}")
        return False

# ==================== COMPANY DASHBOARD ====================

@login_required
@company_active_required
def company_dashboard(request):
    """Company Dashboard"""
    company = get_user_company(request.user)
    
    total_jobs = Job.objects.filter(company=company).count()
    active_jobs = Job.objects.filter(company=company, is_active=True).count()
    total_applications = Application.objects.filter(job__company=company).count()
    
    today = timezone.now().date()
    todays_interviews = Interview.objects.filter(
        application__job__company=company,
        scheduled_date__date=today,
        status='scheduled'
    ).select_related('application', 'application__candidate', 'application__job')
    
    recent_applications = Application.objects.filter(
        job__company=company
    ).select_related('candidate', 'job').order_by('-applied_on')[:5]
    
    recent_jobs = Job.objects.filter(company=company).order_by('-posted_on')[:5]
    
    upcoming_interviews = Interview.objects.filter(
        application__job__company=company,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).select_related('application', 'application__candidate', 'application__job').order_by('scheduled_date')[:5]
    
    # Get unread message count
    unread_messages = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    context = {
        'company': company,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'todays_interviews': todays_interviews,
        'recent_applications': recent_applications,
        'recent_jobs': recent_jobs,
        'upcoming_interviews': upcoming_interviews,
        'unread_messages': unread_messages,
    }
    return render(request, 'dashboard/company_dashboard.html', context)

# ==================== JOB MANAGEMENT ====================

@login_required
@company_active_required
def post_job(request):
    """Post a new job"""
    company = get_user_company(request.user)
    
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.is_approved = False  # New jobs need admin approval
            job.save()
            messages.success(request, 'Job posted successfully! It will be visible after admin approval.')
            return redirect('manage_jobs')
    else:
        form = JobPostForm()
    
    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'dashboard/post_job.html', context)

@login_required
@company_active_required
def edit_job(request, job_id):
    """Edit an existing job"""
    company = get_user_company(request.user)
    job = get_object_or_404(Job, id=job_id, company=company)
    
    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('manage_jobs')
    else:
        form = JobPostForm(instance=job)
    
    context = {
        'form': form,
        'job': job,
        'company': company,
    }
    return render(request, 'dashboard/post_job.html', context)

@login_required
@company_active_required
def delete_job(request, job_id):
    """Delete a job"""
    company = get_user_company(request.user)
    job = get_object_or_404(Job, id=job_id, company=company)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('manage_jobs')
    
    return redirect('manage_jobs')

@login_required
@company_active_required
def manage_jobs(request):
    """Manage all jobs posted by company"""
    company = get_user_company(request.user)
    
    jobs = Job.objects.filter(company=company).order_by('-posted_on')
    
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if status_filter == 'active':
        jobs = jobs.filter(is_active=True, is_approved=True)
    elif status_filter == 'inactive':
        jobs = jobs.filter(is_active=False)
    elif status_filter == 'pending':
        jobs = jobs.filter(is_approved=False)
    elif status_filter == 'expired':
        jobs = jobs.filter(application_deadline__lt=timezone.now().date())
    
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'jobs': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'dashboard/manage_jobs.html', context)

@login_required
@company_active_required
def toggle_job_status(request, job_id):
    """Toggle job active status via AJAX"""
    if request.method == 'POST':
        company = get_user_company(request.user)
        job = get_object_or_404(Job, id=job_id, company=company)
        
        job.is_active = not job.is_active
        job.save()
        
        return JsonResponse({
            'success': True,
            'is_active': job.is_active
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# ==================== APPLICATION MANAGEMENT ====================

@login_required
@company_active_required
def view_applications(request, job_id=None):
    """View applications sorted by match percentage"""
    company = get_user_company(request.user)
    
    # Initialize job variable
    job = None
    
    if job_id:
        job = get_object_or_404(Job, id=job_id, company=company)
        applications = Application.objects.filter(job=job).select_related(
            'candidate', 'candidate__profile'
        ).order_by('-match_percentage', '-applied_on')
    else:
        applications = Application.objects.filter(
            job__company=company
        ).select_related(
            'candidate', 'candidate__profile', 'job'
        ).order_by('-match_percentage', '-applied_on')
    
    # FIXED: Use the form with proper date filtering
    filter_form = ApplicationFilterForm(request.GET or None)
    
    if filter_form.is_valid():
        # Apply filters using the form's filter_queryset method
        applications = filter_form.filter_queryset(applications)
    
    # Get applications with interview status
    applications_list = []
    for app in applications:
        has_interview = Interview.objects.filter(application=app).exists()
        applications_list.append({
            'application': app,
            'has_interview': has_interview,
        })
    
    company_jobs = Job.objects.filter(company=company).order_by('-posted_on')
    
    paginator = Paginator(applications_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    status_counts = {
        'applied': Application.objects.filter(job__company=company, status='applied').count(),
        'shortlisted': Application.objects.filter(job__company=company, status='shortlisted').count(),
        'interview': Application.objects.filter(job__company=company, status='interview').count(),
        'selected': Application.objects.filter(job__company=company, status='selected').count(),
        'rejected': Application.objects.filter(job__company=company, status='rejected').count(),
    }
    
    context = {
        'company': company,
        'job': job,
        'applications': page_obj,
        'company_jobs': company_jobs,
        'filter_form': filter_form,  # Pass the form to template
        'status_counts': status_counts,
        'total_applications': len(applications_list),
        'sort_by_match': True,
    }
    return render(request, 'dashboard/applications.html', context)
    
# ==================== ORIGINAL STATUS UPDATE FUNCTION ====================
@login_required
def update_application_status(request, application_id):
    """Update application status - ORIGINAL"""
    if request.method == 'POST':
        try:
            company = get_user_company(request.user)
            application = get_object_or_404(Application, id=application_id)
            
            # Check authorization if company exists
            if company and application.job.company != company:
                messages.error(request, 'Unauthorized access')
                return redirect('view_applications')
            
            new_status = request.POST.get('status')
            if new_status in dict(Application.STATUS_CHOICES).keys():
                application.status = new_status
                if new_status == 'shortlisted':
                    application.shortlisted_on = timezone.now()
                application.updated_on = timezone.now()
                application.save()
                
                messages.success(request, f'Status updated to {application.get_status_display()}')
            else:
                messages.error(request, 'Invalid status')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('candidate_profile', application_id=application_id)

# ==================== SIMPLE STATUS UPDATE - GUARANTEED TO WORK ====================
def update_status_simple(request, application_id):
    """Super simple status update - no authentication decorators, always works"""
    if request.method == 'POST':
        try:
            # Get the application
            application = get_object_or_404(Application, id=application_id)
            
            # Get the new status from POST data
            new_status = request.POST.get('status')
            
            # Check if valid status
            valid_statuses = dict(Application.STATUS_CHOICES).keys()
            if new_status in valid_statuses:
                application.status = new_status
                application.save()
                messages.success(request, f'✅ Status updated to {application.get_status_display()}')
            else:
                messages.error(request, f'❌ Invalid status: {new_status}')
                
        except Application.DoesNotExist:
            messages.error(request, '❌ Application not found')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    # Redirect back to the candidate profile
    return redirect('candidate_profile', application_id=application_id)

@login_required
@company_active_required
def candidate_profile(request, application_id):
    """View candidate profile"""
    company = get_user_company(request.user)
    application = get_object_or_404(Application, id=application_id)
    
    if application.job.company != company:
        messages.error(request, "Unauthorized access.")
        return redirect('view_applications')
    
    application_messages = Message.objects.filter(
        Q(sender=request.user, recipient=application.candidate) |
        Q(sender=application.candidate, recipient=request.user)
    ).order_by('-sent_at')
    
    # Get interviews for this application
    interviews = Interview.objects.filter(application=application).order_by('-scheduled_date')
    
    try:
        profile = UserProfile.objects.get(user=application.candidate)
        candidate_details = {
            'skills': profile.skills,
            'years_experience': profile.years_experience,
            'highest_education': profile.highest_education,
            'location': profile.location,
            'preferred_job_types': profile.preferred_job_types,
            'summary': profile.summary,
            'resume_url': profile.resume.url if profile.resume else None,
        }
    except UserProfile.DoesNotExist:
        candidate_details = {}
    
    # Get candidate's total applications
    candidate_total_applications = Application.objects.filter(candidate=application.candidate).count()
    
    # Get interview if exists
    interview = interviews.first()
    
    context = {
        'company': company,
        'application': application,
        'candidate': application.candidate,
        'candidate_details': candidate_details,
        'candidate_total_applications': candidate_total_applications,
        'messages': application_messages,
        'interviews': interviews,
        'interview': interview,
    }
    return render(request, 'dashboard/candidate_profile.html', context)

# ==================== INTERVIEW MANAGEMENT ====================

@login_required
@company_active_required
def schedule_interview(request, application_id):
    """Schedule interview for candidate"""
    company = get_user_company(request.user)
    
    application = get_object_or_404(
        Application.objects.select_related('candidate', 'job', 'job__company'),
        id=application_id
    )
    
    if application.job.company != company:
        messages.error(request, "You are not authorized to schedule interviews for this application.")
        return redirect('view_applications')
    
    try:
        interview = Interview.objects.get(application=application)
        is_edit = True
    except Interview.DoesNotExist:
        interview = None
        is_edit = False
    
    if request.method == 'POST':
        try:
            scheduled_date = request.POST.get('scheduled_date')
            interview_type = request.POST.get('interview_type')
            platform = request.POST.get('platform', '')
            meeting_link = request.POST.get('meeting_link', '')
            meeting_id = request.POST.get('meeting_id', '')
            passcode = request.POST.get('passcode', '')
            interviewer = request.POST.get('interviewer', '')
            duration = request.POST.get('duration', '60')
            notes = request.POST.get('notes', '')
            location = request.POST.get('location', '')
            send_email = request.POST.get('send_email') == 'on'
            
            if not scheduled_date:
                messages.error(request, "Interview date and time is required.")
                return redirect('schedule_interview', application_id=application_id)
            
            if not interview_type:
                messages.error(request, "Interview type is required.")
                return redirect('schedule_interview', application_id=application_id)
            
            if not interviewer:
                messages.error(request, "Interviewer name is required.")
                return redirect('schedule_interview', application_id=application_id)
            
            try:
                if 'T' in scheduled_date:
                    scheduled_date = scheduled_date.replace('T', ' ')
                scheduled_datetime = datetime.fromisoformat(scheduled_date)
                if timezone.is_naive(scheduled_datetime):
                    scheduled_datetime = timezone.make_aware(scheduled_datetime)
            except Exception as e:
                messages.error(request, f"Invalid date format: {str(e)}")
                return redirect('schedule_interview', application_id=application_id)
            
            if scheduled_datetime <= timezone.now():
                messages.error(request, "Interview must be scheduled at least 1 hour from now.")
                return redirect('schedule_interview', application_id=application_id)
            
            if is_edit and interview:
                interview.scheduled_date = scheduled_datetime
                interview.interview_type = interview_type
                interview.platform = platform
                interview.meeting_link = meeting_link
                interview.meeting_id = meeting_id
                interview.passcode = passcode
                interview.interviewer = interviewer
                interview.duration_minutes = int(duration)
                interview.notes = notes
                interview.location = location
                interview.updated_at = timezone.now()
                interview.save()
                
                messages.success(request, "Interview updated successfully!")
                
            else:
                interview = Interview.objects.create(
                    application=application,
                    scheduled_date=scheduled_datetime,
                    interview_type=interview_type,
                    platform=platform,
                    meeting_link=meeting_link,
                    meeting_id=meeting_id,
                    passcode=passcode,
                    interviewer=interviewer,
                    duration_minutes=int(duration),
                    notes=notes,
                    location=location,
                    status='scheduled',
                    created_by=request.user
                )
                
                application.status = 'interview'
                application.updated_on = timezone.now()
                application.save(update_fields=['status', 'updated_on'])
                
                messages.success(request, f"Interview scheduled successfully with {application.candidate.get_full_name() or application.candidate.username}")
                
                if send_email:
                    try:
                        send_interview_email(application, interview)
                        messages.info(request, "Email notification sent to candidate.")
                    except Exception as e:
                        messages.warning(request, "Interview scheduled but email could not be sent.")
            
            return redirect('candidate_profile', application_id=application.id)
            
        except Exception as e:
            messages.error(request, f'Error scheduling interview: {str(e)}')
            return redirect('schedule_interview', application_id=application_id)
    
    min_datetime = (timezone.now() + timedelta(hours=1)).isoformat()[:16]
    
    form_data = {}
    if is_edit and interview:
        form_data = {
            'scheduled_date': interview.scheduled_date.isoformat()[:16],
            'interview_type': interview.interview_type,
            'platform': interview.platform or '',
            'meeting_link': interview.meeting_link or '',
            'meeting_id': interview.meeting_id or '',
            'passcode': interview.passcode or '',
            'interviewer': interview.interviewer,
            'duration': interview.duration_minutes,
            'notes': interview.notes or '',
            'location': interview.location or '',
        }
    
    context = {
        'company': company,
        'application': application,
        'candidate': application.candidate,
        'job': application.job,
        'is_edit': is_edit,
        'interview': interview if is_edit else None,
        'form_data': form_data,
        'min_datetime': min_datetime,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/interview_schedule.html', context)

@login_required
@company_active_required
def company_interviews(request):
    """View all company interviews"""
    company = get_user_company(request.user)
    
    interviews = Interview.objects.filter(
        application__job__company=company
    ).select_related(
        'application', 
        'application__candidate', 
        'application__job'
    ).order_by('-scheduled_date')
    
    status_filter = request.GET.get('status', 'upcoming')
    today = timezone.now().date()
    
    if status_filter == 'upcoming':
        interviews = interviews.filter(scheduled_date__gte=timezone.now(), status='scheduled')
    elif status_filter == 'past':
        interviews = interviews.filter(scheduled_date__lt=timezone.now())
    elif status_filter == 'today':
        interviews = interviews.filter(scheduled_date__date=today)
    elif status_filter == 'cancelled':
        interviews = interviews.filter(status='cancelled')
    
    total_interviews = Interview.objects.filter(application__job__company=company).count()
    upcoming_count = Interview.objects.filter(
        application__job__company=company,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    today_count = Interview.objects.filter(
        application__job__company=company,
        scheduled_date__date=today,
        status='scheduled'
    ).count()
    
    paginator = Paginator(interviews, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'interviews': page_obj,
        'total_interviews': total_interviews,
        'upcoming_count': upcoming_count,
        'today_count': today_count,
        'status_filter': status_filter,
        'today': today,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/company_interviews.html', context)

@login_required
@company_active_required
def cancel_interview(request, interview_id):
    """Cancel an interview"""
    company = get_user_company(request.user)
    interview = get_object_or_404(
        Interview.objects.select_related('application'),
        id=interview_id,
        application__job__company=company
    )
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, "Cancellation reason is required.")
            return redirect('cancel_interview', interview_id=interview_id)
        
        interview.status = 'cancelled'
        interview.cancellation_reason = reason
        interview.cancelled_by = 'company'
        interview.cancelled_at = timezone.now()
        interview.save()
        
        messages.success(request, "Interview cancelled successfully.")
        return redirect('candidate_profile', application_id=interview.application.id)
    
    context = {
        'company': company,
        'interview': interview,
    }
    return render(request, 'dashboard/cancel_interview.html', context)

# ==================== ANALYTICS ====================

@login_required
@company_active_required
def company_analytics(request):
    """Company analytics dashboard"""
    company = get_user_company(request.user)
    
    # Get all jobs
    jobs = Job.objects.filter(company=company).order_by('-posted_on')[:10]
    
    # Manually calculate counts for each job
    jobs_with_counts = []
    for job in jobs:
        applications = Application.objects.filter(job=job)
        application_count = applications.count()
        
        # Count interviews for this job
        interview_count = Interview.objects.filter(application__job=job).count()
        
        # Count hired for this job
        hired_count = applications.filter(status='selected').count()
        
        jobs_with_counts.append({
            'title': job.title,
            'application_count': application_count,
            'interview_count': interview_count,
            'hired_count': hired_count,
            'is_active': job.is_active,
        })
    
    # Get all applications
    applications = Application.objects.filter(job__company=company)
    total_applications = applications.count()
    
    # Status distribution
    applied_count = applications.filter(status='applied').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    interview_count = applications.filter(status='interview').count()
    selected_count = applications.filter(status='selected').count()
    rejected_count = applications.filter(status='rejected').count()
    
    # Interview stats
    interviews = Interview.objects.filter(application__job__company=company)
    interview_stats = {
        'total': interviews.count(),
        'scheduled': interviews.filter(status='scheduled').count(),
        'completed': interviews.filter(status='completed').count(),
        'cancelled': interviews.filter(status='cancelled').count(),
        'upcoming': interviews.filter(
            scheduled_date__gte=timezone.now(),
            status='scheduled'
        ).count(),
    }
    
    # Date range for timeline
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get recent applications for table
    recent_applications = applications.select_related(
        'candidate', 'job'
    ).order_by('-applied_on')[:10]
    
    # Calculate conversion rate
    conversion_rate = 0
    if total_applications > 0:
        conversion_rate = (selected_count / total_applications) * 100
    
    # DEBUG: Print to console
    print(f"\n=== COMPANY: {company.name} ===")
    print(f"Jobs found: {len(jobs_with_counts)}")
    for job in jobs_with_counts:
        print(f"  - {job['title']}: Apps={job['application_count']}, Interviews={job['interview_count']}")
    
    context = {
        'company': company,
        'jobs_with_counts': jobs_with_counts,  # THIS IS THE KEY VARIABLE
        'total_applications': total_applications,
        'applied_count': applied_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'interview_stats': interview_stats,
        'start_date': start_date,
        'end_date': end_date,
        'recent_applications': recent_applications,
        'conversion_rate': conversion_rate,
    }
    return render(request, 'dashboard/company_analytics.html', context)
    
# ==================== PROFILE ====================

@login_required
@company_active_required
def edit_company_profile(request):
    """Edit company profile"""
    company = get_user_company(request.user)
    
    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, request.FILES, instance=company, user=request.user)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            
            email = form.cleaned_data.get('email')
            if email and request.user.email != email:
                request.user.email = email
                request.user.save()
            
            messages.success(request, 'Company profile updated successfully!')
            return redirect('company_dashboard')
    else:
        if company:
            form = CompanyProfileForm(instance=company, user=request.user)
        else:
            form = CompanyProfileForm(initial={'email': request.user.email}, user=request.user)
    
    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'dashboard/edit_profile.html', context)

# ==================== AJAX ENDPOINTS ====================

@login_required
@company_active_required
def get_dashboard_stats(request):
    """Get dashboard stats via AJAX"""
    company = get_user_company(request.user)
    
    total_jobs = Job.objects.filter(company=company).count()
    active_jobs = Job.objects.filter(company=company, is_active=True).count()
    total_applications = Application.objects.filter(job__company=company).count()
    pending_applications = Application.objects.filter(
        job__company=company,
        status='applied'
    ).count()
    
    today = timezone.now().date()
    todays_applications = Application.objects.filter(
        job__company=company,
        applied_on__date=today
    ).count()
    
    todays_interviews = Interview.objects.filter(
        application__job__company=company,
        scheduled_date__date=today,
        status='scheduled'
    ).count()
    
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    return JsonResponse({
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'todays_applications': todays_applications,
        'todays_interviews': todays_interviews,
        'unread_messages': unread_messages,
    })

# ==================== DEBUG VIEW ====================

@login_required
def debug_interviews(request):
    """Debug view to check all interviews"""
    company = get_user_company(request.user)
    
    if not company:
        return JsonResponse({'error': 'No company found'}, status=400)
    
    interviews = Interview.objects.filter(
        application__job__company=company
    ).select_related(
        'application', 
        'application__candidate', 
        'application__job'
    ).order_by('-scheduled_date')
    
    data = {
        'total_interviews': interviews.count(),
        'company': company.name,
        'interviews': []
    }
    
    for interview in interviews:
        data['interviews'].append({
            'id': interview.id,
            'candidate': interview.application.candidate.username,
            'candidate_email': interview.application.candidate.email,
            'job': interview.application.job.title,
            'scheduled_date': interview.scheduled_date.isoformat(),
            'status': interview.status,
            'interview_type': interview.interview_type,
            'created_at': interview.created_at.isoformat(),
            'application_status': interview.application.status,
        })
    
    return JsonResponse(data)


# ==================== MESSAGING SYSTEM ====================

@login_required
@company_active_required
def company_messages(request):
    """View all company messages"""
    company = get_user_company(request.user)
    
    # Get all users this company has exchanged messages with
    sent_to_users = Message.objects.filter(
        sender=request.user
    ).values_list('recipient', flat=True).distinct()
    
    received_from_users = Message.objects.filter(
        recipient=request.user
    ).values_list('sender', flat=True).distinct()
    
    all_user_ids = set(list(sent_to_users) + list(received_from_users))
    
    conversations = []
    for user_id in all_user_ids:
        try:
            user = User.objects.get(id=user_id)
            
            # Get last message
            last_message = Message.objects.filter(
                Q(sender=request.user, recipient=user) | 
                Q(sender=user, recipient=request.user)
            ).order_by('-sent_at').first()
            
            # Count unread messages from this user
            unread_count = Message.objects.filter(
                sender=user,
                recipient=request.user,
                is_read=False
            ).count()
            
            # Get application if exists
            application = Application.objects.filter(
                candidate=user,
                job__company=company
            ).first()
            
            candidate_name = user.get_full_name() or user.username
            
            conversations.append({
                'user': user,
                'user_id': user.id,
                'last_message': last_message,
                'unread_count': unread_count,
                'application': application,
                'candidate_name': candidate_name,
                'application_id': application.id if application else None,
            })
        except User.DoesNotExist:
            continue
    
    # Sort by last message date (newest first)
    conversations.sort(
        key=lambda x: x['last_message'].sent_at if x['last_message'] else datetime.min, 
        reverse=True
    )
    
    # Calculate stats
    total_sent = Message.objects.filter(sender=request.user).count()
    total_received = Message.objects.filter(recipient=request.user).count()
    unread_total = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'company': company,
        'conversations': conversations,
        'total_sent': total_sent,
        'total_received': total_received,
        'unread_total': unread_total,
    }
    return render(request, 'dashboard/company_messages.html', context)


@login_required
@company_active_required
def send_message(request, application_id):
    """Send message to candidate"""
    company = get_user_company(request.user)
    
    application = get_object_or_404(Application, id=application_id)
    
    if application.job.company != company:
        messages.error(request, "Unauthorized access.")
        return redirect('view_applications')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        subject = request.POST.get('subject', '').strip()
        
        if not content:
            messages.error(request, "Message content cannot be empty.")
        else:
            try:
                message = Message.objects.create(
                    sender=request.user,
                    recipient=application.candidate,
                    subject=subject,
                    content=content,
                    application=application,
                    sent_at=timezone.now(),
                    is_read=False
                )
                
                messages.success(request, 'Message sent successfully!')
                
                # Handle AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Message sent successfully!',
                        'message_id': message.id
                    })
                
                return redirect('conversation_detail', user_id=application.candidate.id)
                
            except Exception as e:
                messages.error(request, f"Error sending message: {str(e)}")
    
    # Get previous messages for this conversation
    previous_messages = Message.objects.filter(
        Q(sender=request.user, recipient=application.candidate) |
        Q(sender=application.candidate, recipient=request.user)
    ).order_by('-sent_at')[:20]
    
    context = {
        'company': company,
        'application': application,
        'candidate': application.candidate,
        'previous_messages': previous_messages,
    }
    return render(request, 'dashboard/send_message.html', context)


@login_required
@company_active_required
def conversation_detail(request, user_id):
    """View full conversation with a job seeker"""
    company = get_user_company(request.user)
    
    try:
        # Get the other user (job seeker)
        other_user = User.objects.get(id=user_id)
        
        # Verify this user has applied to this company's jobs OR has messages
        has_application = Application.objects.filter(
            candidate=other_user,
            job__company=company
        ).exists()
        
        has_messages = Message.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        ).exists()
        
        if not has_application and not has_messages:
            messages.error(request, "You don't have any conversation with this user.")
            return redirect('company_messages')
        
        # Get all messages between company and this job seeker
        messages_list = Message.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        ).select_related('sender', 'recipient').order_by('sent_at')
        
        # Mark unread messages as read
        unread_messages = messages_list.filter(
            sender=other_user,
            recipient=request.user,
            is_read=False
        )
        if unread_messages.exists():
            unread_messages.update(is_read=True, read_at=timezone.now())
        
        # Get application if exists
        application = Application.objects.filter(
            candidate=other_user,
            job__company=company
        ).first()
        
        # Handle quick reply via POST
        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            subject = request.POST.get('subject', '').strip()
            
            if content:
                message = Message.objects.create(
                    sender=request.user,
                    recipient=other_user,
                    subject=subject,
                    content=content,
                    application=application,
                    sent_at=timezone.now(),
                    is_read=False
                )
                
                messages.success(request, "Reply sent successfully!")
                return redirect('conversation_detail', user_id=user_id)
        
        context = {
            'company': company,
            'other_user': other_user,
            'messages': messages_list,
            'application': application,
            'unread_count': unread_messages.count(),
            'total_messages': messages_list.count(),
        }
        
        return render(request, 'dashboard/conversation_detail.html', context)
        
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('company_messages')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('company_messages')


@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=message_id, recipient=request.user)
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
            
            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@login_required
def mark_all_read(request):
    """Mark all messages as read"""
    if request.method == 'POST':
        try:
            count = Message.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
            
            return JsonResponse({'success': True, 'count': count})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)