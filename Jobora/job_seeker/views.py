from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from datetime import datetime, timedelta, date
import json
import re

# ==================== CORRECTED IMPORTS ====================
from users.models import UserProfile, SavedJob
from jobs.models import Company, Job, Application, Interview, Message, JobCategory
from users.forms import UserProfileForm, ApplicationForm, JobSearchForm
from users.job_seeker_decorators import job_seeker_required
from ai.matcher import ResumeJobMatcher

# ==================== DECORATORS ====================
def job_seeker_required_old(view_func):
    """Decorator to ensure user has a job seeker profile"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            UserProfile.objects.get(user=request.user)
            return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            messages.error(request, "Please complete your profile first.")
            return redirect('edit_job_seeker_profile')
    return wrapper

# ==================== HELPER FUNCTIONS ====================
def get_recommended_jobs(user):
    """Get personalized job recommendations with AI match scores"""
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return []
    
    # Get user's preferences
    preferred_job_types = profile.preferred_job_types.split(',') if profile.preferred_job_types else []
    skills = set([s.strip().lower() for s in profile.skills.split(',') if s.strip()]) if profile.skills else set()
    location = profile.location.lower() if profile.location else ''
    
    # Get all active jobs
    jobs = Job.objects.filter(is_active=True, is_approved=True).select_related('company')
    
    recommended_jobs = []
    
    for job in jobs:
        match_score = 0
        matching_skills = []
        
        # 1. Job type match (30 points)
        if preferred_job_types and job.job_type in preferred_job_types:
            match_score += 30
        
        # 2. Skills match (40 points)
        if skills and job.skills_required:
            job_skills = set([s.strip().lower() for s in job.skills_required.split(',') if s.strip()])
            if job_skills:
                matched = skills.intersection(job_skills)
                matching_skills = list(matched)[:5]
                if len(job_skills) > 0:
                    match_score += (len(matched) / len(job_skills)) * 40
        
        # 3. Location match (30 points)
        if location and job.location:
            if location in job.location.lower() or job.location.lower() in location:
                match_score += 30
            elif job.is_remote:
                match_score += 20
        
        # Only include jobs with at least 10% match
        if match_score >= 10:
            # Add match score as an attribute to the job object
            job.ai_match_score = int(match_score)
            job.matching_skills = matching_skills
            recommended_jobs.append(job)
    
    # Sort by match score (highest first)
    recommended_jobs.sort(key=lambda x: x.ai_match_score, reverse=True)
    
    return recommended_jobs[:10]  # Return top 10

def calculate_profile_completion(profile):
    """Calculate profile completion percentage"""
    if not profile:
        return 0
    
    total_score = 0
    max_score = 100
    
    # Required fields (60 points)
    if profile.user.first_name: total_score += 8
    if profile.user.last_name: total_score += 8
    if profile.user.email: total_score += 8
    if profile.phone: total_score += 8
    if profile.location: total_score += 8
    if profile.user_type: total_score += 5
    if profile.highest_education: total_score += 5
    if profile.skills: total_score += 5
    if profile.preferred_job_types: total_score += 5
    
    # Optional fields (40 points)
    if profile.profile_picture: total_score += 5
    if profile.resume: total_score += 10
    if profile.summary: total_score += 5
    if profile.headline: total_score += 5
    if profile.current_role: total_score += 5
    if profile.years_experience and profile.years_experience > 0: total_score += 5
    if profile.preferred_locations: total_score += 5
    
    return min(total_score, max_score)

# ==================== CONSTANTS ====================
JOB_TYPE_CHOICES = [
    ('full_time', 'Full-time'),
    ('part_time', 'Part-time'),
    ('internship', 'Internship'),
    ('freelance', 'Freelance/Contract'),
]

AVAILABILITY_CHOICES = [
    ('immediate', 'Immediately Available'),
    ('2_weeks', 'Available in 2 Weeks'),
    ('1_month', 'Available in 1 Month'),
    ('notice_period', 'Serving Notice Period'),
    ('not_available', 'Not Available'),
]

WORK_PREFERENCE_CHOICES = [
    ('office', 'Office Only'),
    ('hybrid', 'Hybrid'),
    ('remote', 'Remote Only'),
    ('flexible', 'Flexible'),
]

SEARCH_INTENSITY_CHOICES = [
    ('casual', 'Casual Search'),
    ('active', 'Active Search'),
    ('urgent', 'Urgent - Need Job ASAP'),
]

COMPANY_SIZE_CHOICES = [
    ('startup', 'Startup (1-50 employees)'),
    ('small', 'Small (51-200 employees)'),
    ('medium', 'Medium (201-1000 employees)'),
    ('large', 'Large (1000+ employees)'),
    ('any', 'Any Size'),
]

# ==================== EDIT PROFILE VIEW ====================
@login_required
@job_seeker_required
def edit_job_seeker_profile(request):
    """Edit Job Seeker Profile"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Create minimal profile
        profile = UserProfile.objects.create(
            user=request.user,
            user_type='fresher'
        )
    
    # Max date for DOB (18 years ago)
    max_date = date.today().replace(year=date.today().year - 18).isoformat()
    
    # Constants for template
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance/Contract'),
    ]
    
    USER_TYPES = [
        ('fresher', 'Fresher (0-1 years)'),
        ('experienced', 'Experienced (1+ years)'),
        ('intern', 'Intern'),
    ]
    
    EDUCATION_LEVELS = [
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('phd', 'Ph.D.'),
    ]
    
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '')
        location = request.POST.get('location', '').strip()
        user_type = request.POST.get('user_type', '').strip()
        current_role = request.POST.get('current_role', '').strip()
        current_company = request.POST.get('current_company', '').strip()
        years_experience = request.POST.get('years_experience', '0').strip()
        summary = request.POST.get('summary', '').strip()
        highest_education = request.POST.get('highest_education', '').strip()
        field_of_study = request.POST.get('field_of_study', '').strip()
        institution = request.POST.get('institution', '').strip()
        graduation_year = request.POST.get('graduation_year', '').strip()
        skills = request.POST.get('skills', '').strip()
        preferred_locations = request.POST.get('preferred_locations', '').strip()
        expected_salary = request.POST.get('expected_salary', '').strip()
        linkedin_profile = request.POST.get('linkedin_profile', '').strip()
        github_profile = request.POST.get('github_profile', '').strip()
        portfolio_link = request.POST.get('portfolio_link', '').strip()
        
        # Get preferred job types as list
        preferred_job_types = request.POST.getlist('preferred_job_types', [])
        
        # Validate required fields
        errors = []
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not phone:
            errors.append('Phone number is required')
        if not location:
            errors.append('Location is required')
        if not user_type:
            errors.append('User type is required')
        if not highest_education:
            errors.append('Highest education is required')
        if not skills:
            errors.append('Skills are required')
        if not preferred_job_types:
            errors.append('At least one job type preference is required')
        
        # Validate phone number
        phone_pattern = r'^[6-9]\d{9}$'
        if phone and not re.match(phone_pattern, phone):
            errors.append('Please enter a valid 10-digit Indian mobile number')
        
        # Validate date of birth (18+)
        if date_of_birth:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                errors.append('You must be at least 18 years old')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Update User model
                user = request.user
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                
                # Update profile
                profile.phone = phone
                profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
                profile.location = location
                profile.summary = summary
                profile.user_type = user_type
                profile.current_role = current_role
                profile.current_company = current_company
                profile.years_experience = int(years_experience) if years_experience.isdigit() else 0
                profile.highest_education = highest_education
                profile.field_of_study = field_of_study
                profile.institution = institution
                profile.graduation_year = int(graduation_year) if graduation_year.isdigit() else None
                profile.skills = skills
                profile.preferred_locations = preferred_locations
                profile.salary_expectation = float(expected_salary) if expected_salary and expected_salary.replace('.', '').isdigit() else None
                profile.linkedin_profile = linkedin_profile
                profile.github_profile = github_profile
                profile.portfolio_link = portfolio_link
                
                # Handle file uploads
                if 'profile_picture' in request.FILES:
                    profile.profile_picture = request.FILES['profile_picture']
                
                if 'resume' in request.FILES:
                    profile.resume = request.FILES['resume']
                
                # Handle file removals
                if request.POST.get('profile_picture-clear') == '1':
                    if profile.profile_picture:
                        profile.profile_picture.delete(save=False)
                    profile.profile_picture = None
                
                # Save preferred job types
                profile.preferred_job_types = ','.join(preferred_job_types)
                
                # Calculate completion
                completion = calculate_profile_completion(profile)
                profile.is_profile_complete = (completion >= 80)
                
                profile.save()
                messages.success(request, '✅ Profile updated successfully!')
                return redirect('job_seeker_dashboard')
                
            except Exception as e:
                messages.error(request, f'❌ Error saving profile: {str(e)}')
    
    # Prepare context
    preferred_job_types_list = []
    if profile.preferred_job_types:
        preferred_job_types_list = [t.strip() for t in profile.preferred_job_types.split(',') if t.strip()]
    
    current_completion = calculate_profile_completion(profile)
    
    # Simple form object for template
    class SimpleForm:
        def __init__(self, profile):
            self.first_name = profile.user.first_name
            self.last_name = profile.user.last_name
            self.phone = profile.phone
            self.date_of_birth = profile.date_of_birth
            self.location = profile.location
            self.summary = profile.summary
            self.user_type = profile.user_type
            self.current_role = profile.current_role
            self.current_company = profile.current_company
            self.years_experience = profile.years_experience
            self.highest_education = profile.highest_education
            self.field_of_study = profile.field_of_study
            self.institution = profile.institution
            self.graduation_year = profile.graduation_year
            self.skills = profile.skills
            self.preferred_locations = profile.preferred_locations
            self.expected_salary = profile.salary_expectation
            self.linkedin_profile = profile.linkedin_profile
            self.github_profile = profile.github_profile
            self.portfolio_link = profile.portfolio_link
            
        def get(self, key, default=''):
            return getattr(self, key, default)
    
    form = SimpleForm(profile)
    
    context = {
        'job_seeker': profile,
        'form': form,
        'profile_completion': current_completion,
        'preferred_job_types_list': preferred_job_types_list,
        'JOB_TYPE_CHOICES': JOB_TYPE_CHOICES,
        'USER_TYPES': USER_TYPES,
        'EDUCATION_LEVELS': EDUCATION_LEVELS,
        'max_date': max_date,
    }
    
    return render(request, 'dashboard/job_seeker/edit_profile.html', context)

# ==================== DASHBOARD VIEW ====================
@login_required
@job_seeker_required
def job_seeker_dashboard(request):
    """Job Seeker Dashboard"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile.")
        return redirect('edit_job_seeker_profile')
    
    # Application counts
    total_applications = Application.objects.filter(candidate=request.user).count()
    pending_applications = Application.objects.filter(
        candidate=request.user, 
        status__in=['applied', 'shortlisted']
    ).count()
    
    # Interview counts
    upcoming_interviews = Interview.objects.filter(
        application__candidate=request.user,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    
    # Message counts
    unread_messages = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Saved jobs count
    saved_jobs_count = SavedJob.objects.filter(user=request.user, is_active=True).count()
    
    # Recent applications
    recent_applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job', 'job__company').order_by('-applied_on')[:5]
    
    # ===== FIXED: Get AI-recommended jobs with match scores =====
    recommended_jobs = get_recommended_jobs(request.user)
    
    # Upcoming interviews list
    upcoming_interviews_list = Interview.objects.filter(
        application__candidate=request.user,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).select_related('application', 'application__job', 'application__job__company').order_by('scheduled_date')[:3]
    
    # Profile completion
    profile_completion = calculate_profile_completion(profile)
    
    # Status counts for funnel
    shortlisted_count = Application.objects.filter(
        candidate=request.user,
        status='shortlisted'
    ).count()
    
    interview_count = Application.objects.filter(
        candidate=request.user,
        status='interview'
    ).count()
    
    selected_count = Application.objects.filter(
        candidate=request.user,
        status='selected'
    ).count()
    
    rejected_count = Application.objects.filter(
        candidate=request.user,
        status='rejected'
    ).count()
    
    # Calculate success rate
    if total_applications > 0:
        success_rate = round((selected_count / total_applications) * 100)
    else:
        success_rate = 0
    
    # Calculate interview rate
    if total_applications > 0:
        interview_rate = round(((shortlisted_count + interview_count) / total_applications) * 100)
    else:
        interview_rate = 0
    
    context = {
        'profile': profile,
        'stats': {
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'upcoming_interviews': upcoming_interviews,
            'unread_messages': unread_messages,
            'profile_completion': profile_completion,
            'saved_jobs_count': saved_jobs_count,
            'shortlisted_count': shortlisted_count,
            'interview_count': interview_count,
            'selected_count': selected_count,
            'rejected_count': rejected_count,
            'success_rate': success_rate,
            'interview_rate': interview_rate,
        },
        'recent_applications': recent_applications,
        'recommended_jobs': recommended_jobs,  # Now with ai_match_score
        'upcoming_interviews_list': upcoming_interviews_list,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'success_rate': success_rate,
        'interview_rate': interview_rate,
    }
    return render(request, 'dashboard/job_seeker/dashboard.html', context)


# ==================== VIEW JOB DETAIL ====================
@login_required
@job_seeker_required
def view_job_detail(request, job_id):
    """View detailed job information"""
    job = get_object_or_404(Job, id=job_id, is_active=True, is_approved=True)
    
    today = timezone.now().date()
    deadline_passed = False
    if job.application_deadline:
        deadline_passed = job.application_deadline < today
    
    has_applied = False
    user_application = None
    
    try:
        user_application = Application.objects.get(
            job=job, 
            candidate=request.user
        )
        has_applied = True
    except Application.DoesNotExist:
        pass
    
    is_saved = SavedJob.objects.filter(
        user=request.user,
        job=job,
        is_active=True
    ).exists()
    
    similar_jobs = Job.objects.filter(
        Q(category=job.category) | Q(job_type=job.job_type) | Q(location__icontains=job.location),
        is_active=True,
        is_approved=True,
        application_deadline__gte=today
    ).exclude(id=job.id)[:4]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'user_application': user_application,
        'is_saved': is_saved,
        'similar_jobs': similar_jobs,
        'deadline_passed': deadline_passed,
        'today': today,
    }
    return render(request, 'dashboard/job_seeker/job_detail.html', context)

# ==================== APPLY JOB ====================
@login_required
@job_seeker_required
def apply_job(request, job_id):
    """Apply for a job - with AI matching"""
    job = get_object_or_404(Job, id=job_id, is_active=True, is_approved=True)
    
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('view_job_detail', job_id=job_id)
    
    today = timezone.now().date()
    if job.application_deadline and job.application_deadline < today:
        messages.error(request, "Application deadline has passed.")
        return redirect('view_job_detail', job_id=job_id)
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.resume:
            messages.warning(request, "Please upload your resume before applying.")
            return redirect('edit_job_seeker_profile')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile before applying.")
        return redirect('edit_job_seeker_profile')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create application
            application = Application(
                job=job,
                candidate=request.user,
                cover_letter=form.cleaned_data['cover_letter'],
                expected_salary=form.cleaned_data.get('expected_salary'),
                status='applied',
                applied_on=timezone.now()
            )
            
            # Add resume
            if 'resume' in request.FILES:
                application.resume = request.FILES['resume']
            elif profile.resume:
                application.resume = profile.resume
            
            # Save first to get ID
            application.save()
            
            # ===== AI MATCHING CALCULATION =====
            try:
                matcher = ResumeJobMatcher()
                scores = matcher.calculate_final_score(application)
                
                # Update application with scores
                application.rule_score = scores['rule_score']
                application.ai_score = scores['ai_score']
                application.match_percentage = scores['percentage']
                application.save()
                
                print(f"✅ AI Match: {scores['percentage']}% for {request.user.username}")
                
            except Exception as e:
                print(f"⚠️ AI matching error: {e}")
                # Application still submitted even if AI fails
            
            # Update profile counter
            profile.total_applications += 1
            profile.save()
            
            messages.success(request, "✅ Application submitted successfully!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'application_id': application.id,
                    'message': 'Application submitted successfully!'
                })
            
            return redirect('my_applications')
        else:
            messages.error(request, "❌ Please correct the errors in the form.")
    else:
        # Your existing GET code
        initial_data = {
            'cover_letter': f"Dear Hiring Manager,\n\nI am writing to apply for the {job.title} position at {job.company.name}..."
        }
        form = ApplicationForm(initial=initial_data)
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'dashboard/job_seeker/apply_job.html', context)

@login_required
@job_seeker_required
def search_jobs(request):
    """Search and filter jobs"""
    # Base queryset - get ALL active and approved jobs
    jobs = Job.objects.filter(is_active=True, is_approved=True).order_by('-posted_on')
    
    # Get filter parameters
    keywords = request.GET.get('keywords', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    experience_level = request.GET.get('experience_level', '').strip()
    salary_range = request.GET.get('salary_range', '').strip()
    
    # Apply filters
    if keywords:
        jobs = jobs.filter(
            Q(title__icontains=keywords) |
            Q(description__icontains=keywords) |
            Q(skills_required__icontains=keywords) |
            Q(company__name__icontains=keywords)
        )
    
    if location:
        jobs = jobs.filter(
            Q(location__icontains=location) | Q(is_remote=True)
        )
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if experience_level:
        jobs = jobs.filter(experience_level__iexact=experience_level)
    
    # FIXED: Salary filtering - Convert monthly salary to annual LPA
    # Your database stores monthly salary (10000 = 10,000 per month)
    # Annual LPA = (monthly salary * 12) / 100000
    if salary_range:
        if salary_range == '0-3':
            # 0-3 LPA annual = 0 to 25,000 per month
            jobs = jobs.filter(salary_min__lte=25000)
        elif salary_range == '3-6':
            # 3-6 LPA annual = 25,000 to 50,000 per month
            jobs = jobs.filter(salary_min__gte=25000, salary_min__lte=50000)
        elif salary_range == '6-10':
            # 6-10 LPA annual = 50,000 to 83,333 per month
            jobs = jobs.filter(salary_min__gte=50000, salary_min__lte=83333)
        elif salary_range == '10-15':
            # 10-15 LPA annual = 83,333 to 125,000 per month
            jobs = jobs.filter(salary_min__gte=83333, salary_min__lte=125000)
        elif salary_range == '15-20':
            # 15-20 LPA annual = 125,000 to 166,666 per month
            jobs = jobs.filter(salary_min__gte=125000, salary_min__lte=166666)
        elif salary_range == '20+':
            # 20+ LPA annual = 166,666+ per month
            jobs = jobs.filter(salary_min__gte=166666)
    
    # Get user's applications
    applied_job_ids = []
    user_applications = {}
    
    applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job')
    
    for app in applications:
        applied_job_ids.append(app.job_id)
        user_applications[app.job_id] = app
    
    saved_job_ids = SavedJob.objects.filter(
        user=request.user,
        is_active=True
    ).values_list('job_id', flat=True)
    
    # Calculate profile completion
    profile_completion = 0
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile_completion = calculate_profile_completion(profile)
    except UserProfile.DoesNotExist:
        profile_completion = 0
    
    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        'jobs': page_obj,
        'total_jobs': jobs.count(),
        'applied_job_ids': list(applied_job_ids),
        'saved_job_ids': list(saved_job_ids),
        'user_applications': user_applications,
        'keywords': keywords,
        'location': location,
        'job_type': job_type,
        'experience_level': experience_level,
        'salary_range': salary_range,
        'profile_completion': profile_completion,
    }
    return render(request, 'dashboard/job_seeker/search_jobs.html', context)
# ==================== VIEW JOB DETAIL ====================
@login_required
@job_seeker_required
def view_job_detail(request, job_id):
    """View detailed job information"""
    job = get_object_or_404(Job, id=job_id, is_active=True, is_approved=True)
    
    today = timezone.now().date()
    deadline_passed = False
    if job.application_deadline:
        deadline_passed = job.application_deadline < today
    
    has_applied = False
    user_application = None
    
    try:
        user_application = Application.objects.get(
            job=job, 
            candidate=request.user
        )
        has_applied = True
    except Application.DoesNotExist:
        pass
    
    is_saved = SavedJob.objects.filter(
        user=request.user,
        job=job,
        is_active=True
    ).exists()
    
    similar_jobs = Job.objects.filter(
        Q(category=job.category) | Q(job_type=job.job_type) | Q(location__icontains=job.location),
        is_active=True,
        is_approved=True,
        application_deadline__gte=today
    ).exclude(id=job.id)[:4]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'user_application': user_application,
        'is_saved': is_saved,
        'similar_jobs': similar_jobs,
        'deadline_passed': deadline_passed,
        'today': today,
    }
    return render(request, 'dashboard/job_seeker/job_detail.html', context)

# ==================== APPLY JOB ====================
@login_required
@job_seeker_required
def apply_job(request, job_id):
    """Apply for a job - with AI matching"""
    job = get_object_or_404(Job, id=job_id, is_active=True, is_approved=True)
    
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('view_job_detail', job_id=job_id)
    
    today = timezone.now().date()
    if job.application_deadline and job.application_deadline < today:
        messages.error(request, "Application deadline has passed.")
        return redirect('view_job_detail', job_id=job_id)
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.resume:
            messages.warning(request, "Please upload your resume before applying.")
            return redirect('edit_job_seeker_profile')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile before applying.")
        return redirect('edit_job_seeker_profile')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create application
            application = Application(
                job=job,
                candidate=request.user,
                cover_letter=form.cleaned_data['cover_letter'],
                expected_salary=form.cleaned_data.get('expected_salary'),
                status='applied',
                applied_on=timezone.now()
            )
            
            # Add resume
            if 'resume' in request.FILES:
                application.resume = request.FILES['resume']
            elif profile.resume:
                application.resume = profile.resume
            
            # Save first to get ID
            application.save()
            
            # ===== AI MATCHING CALCULATION =====
            try:
                matcher = ResumeJobMatcher()
                scores = matcher.calculate_final_score(application)
                
                # Update application with scores
                application.rule_score = scores['rule_score']
                application.ai_score = scores['ai_score']
                application.match_percentage = scores['percentage']
                application.save()
                
                print(f"✅ AI Match: {scores['percentage']}% for {request.user.username}")
                
            except Exception as e:
                print(f"⚠️ AI matching error: {e}")
                # Application still submitted even if AI fails
            
            # Update profile counter
            profile.total_applications += 1
            profile.save()
            
            messages.success(request, "✅ Application submitted successfully!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'application_id': application.id,
                    'message': 'Application submitted successfully!'
                })
            
            return redirect('my_applications')
        else:
            messages.error(request, "❌ Please correct the errors in the form.")
    else:
        # Your existing GET code
        initial_data = {
            'cover_letter': f"Dear Hiring Manager,\n\nI am writing to apply for the {job.title} position at {job.company.name}..."
        }
        form = ApplicationForm(initial=initial_data)
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'dashboard/job_seeker/apply_job.html', context)

# ==================== MY APPLICATIONS ====================
@login_required
@job_seeker_required
def my_applications(request):
    """View all applications"""
    status_filter = request.GET.get('status', '')
    job_type_filter = request.GET.get('job_type', '')
    search_query = request.GET.get('search', '')
    
    applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job', 'job__company')
    
    # Apply filters
    if status_filter:
        ALLOWED_STATUSES = ['applied', 'shortlisted', 'interview', 'selected', 'rejected', 'withdrawn']
        if status_filter in ALLOWED_STATUSES:
            applications = applications.filter(status=status_filter)
        else:
            status_filter = ''
    
    if job_type_filter:
        applications = applications.filter(job__job_type=job_type_filter)
    
    if search_query:
        applications = applications.filter(
            Q(job__title__icontains=search_query) |
            Q(job__company__name__icontains=search_query)
        )
    
    total_applications = applications.count()
    applied_count = applications.filter(status='applied').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    interview_count = applications.filter(status='interview').count()
    selected_count = applications.filter(status='selected').count()
    rejected_count = applications.filter(status='rejected').count()
    withdrawn_count = applications.filter(status='withdrawn').count()
    pending_applications = applied_count + shortlisted_count
    
    # Calculate success rate
    if total_applications > 0:
        success_rate = round((selected_count / total_applications) * 100, 1)
    else:
        success_rate = 0
    
    # Calculate interview conversion rate
    if total_applications > 0:
        interview_conversion_rate = round(((shortlisted_count + interview_count) / total_applications) * 100, 1)
    else:
        interview_conversion_rate = 0
    
    # Status counts dictionary
    status_counts = {
        'applied': applied_count,
        'shortlisted': shortlisted_count,
        'interview': interview_count,
        'selected': selected_count,
        'rejected': rejected_count,
        'withdrawn': withdrawn_count,
    }
    
    paginator = Paginator(applications.order_by('-applied_on'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'status_filter': status_filter,
        'job_type_filter': job_type_filter,
        'search_query': search_query,
        'status_counts': status_counts,
        'total_applications': total_applications,
        'applied_count': applied_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'withdrawn_count': withdrawn_count,
        'pending_applications': pending_applications,
        'success_rate': success_rate,
        'interview_conversion_rate': interview_conversion_rate,
        'avg_response_days': '5-7',
    }
    return render(request, 'dashboard/job_seeker/my_applications.html', context)

# ==================== APPLICATION DETAIL ====================
@login_required
@job_seeker_required
def application_detail(request, application_id):
    """View application details"""
    application = get_object_or_404(
        Application.objects.select_related('job', 'job__company'),
        id=application_id, 
        candidate=request.user
    )
    
    interview = None
    try:
        interview = Interview.objects.filter(application=application).first()
    except Interview.DoesNotExist:
        pass
    
    context = {
        'application': application,
        'interview': interview,
    }
    return render(request, 'dashboard/job_seeker/application_detail.html', context)

# ==================== VIEW COMPANY PROFILE ====================
@login_required
@job_seeker_required
def view_company_profile(request, company_id):
    """View company profile"""
    company = get_object_or_404(Company, id=company_id)
    
    today = timezone.now().date()
    active_jobs = Job.objects.filter(
        company=company,
        is_active=True,
        is_approved=True,
        application_deadline__gte=today
    )[:10]
    
    context = {
        'company': company,
        'active_jobs': active_jobs,
        'today': today,
    }
    return render(request, 'dashboard/job_seeker/company_profile.html', context)

@login_required
@job_seeker_required
def my_interviews(request):
    """View all interviews"""
    status_filter = request.GET.get('status', 'upcoming')
    
    VALID_STATUS_FILTERS = ['upcoming', 'past', 'cancelled', 'all']
    if status_filter not in VALID_STATUS_FILTERS:
        status_filter = 'upcoming'
    
    # Base queryset
    interviews = Interview.objects.filter(
        application__candidate=request.user
    ).select_related(
        'application', 
        'application__job', 
        'application__job__company'
    ).order_by('-scheduled_date')
    
    # Statistics for cards
    total_interviews = interviews.count()
    
    # Count interviews by status
    scheduled_count = interviews.filter(status='scheduled').count()
    completed_count = interviews.filter(status='completed').count()
    cancelled_count = interviews.filter(status='cancelled').count()
    
    # Calculate success rate
    success_rate = 0
    if total_interviews > 0:
        success_rate = round((completed_count / total_interviews) * 100)
    
    # Today and tomorrow filters
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    today_interviews = interviews.filter(
        scheduled_date__date=today,
        status='scheduled'
    ).order_by('scheduled_date')
    
    tomorrow_interviews = interviews.filter(
        scheduled_date__date=tomorrow,
        status='scheduled'
    ).order_by('scheduled_date')
    
    # PAST INTERVIEWS (for reference)
    past_scheduled_interviews = interviews.filter(
        scheduled_date__lt=timezone.now(),
        status='scheduled'
    ).order_by('-scheduled_date')
    
    # Apply status filter based on user selection
    if status_filter == 'upcoming':
        # Show ALL scheduled interviews (both past and future)
        # But we'll mark past ones differently in the template
        interviews = interviews.filter(
            status='scheduled'
        ).order_by('-scheduled_date')
    elif status_filter == 'past':
        # Show only past interviews (any status except scheduled future)
        interviews = interviews.filter(
            scheduled_date__lt=timezone.now()
        ).exclude(status='cancelled').order_by('-scheduled_date')
    elif status_filter == 'cancelled':
        interviews = interviews.filter(
            status='cancelled'
        ).order_by('-scheduled_date')
    elif status_filter == 'all':
        # Show all interviews regardless of status
        interviews = interviews.all().order_by('-scheduled_date')
    
    # Pagination
    paginator = Paginator(interviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'interviews': page_obj,
        'today_interviews': today_interviews,
        'tomorrow_interviews': tomorrow_interviews,
        'past_scheduled_interviews': past_scheduled_interviews,
        'status_filter': status_filter,
        'total_interviews': total_interviews,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'success_rate': success_rate,
        'today': today,
        'now': timezone.now(),  # Pass current time to template for comparison
    }
    return render(request, 'dashboard/job_seeker/interviews.html', context)
# ==================== INTERVIEW DETAIL ====================
@login_required
@job_seeker_required
def interview_detail(request, interview_id):
    """View interview details"""
    interview = get_object_or_404(
        Interview.objects.select_related('application', 'application__job', 'application__job__company'),
        id=interview_id,
        application__candidate=request.user
    )
    
    can_cancel = False
    if interview.status == 'scheduled':
        time_until = interview.scheduled_date - timezone.now()
        can_cancel = time_until > timedelta(hours=2)
    
    context = {
        'interview': interview,
        'can_cancel': can_cancel,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/job_seeker/interview_detail.html', context)

# ==================== CANCEL INTERVIEW ====================
@login_required
@job_seeker_required
def cancel_interview(request, interview_id):
    """Cancel an interview"""
    interview = get_object_or_404(
        Interview, 
        id=interview_id,
        application__candidate=request.user
    )
    
    if interview.status != 'scheduled':
        messages.error(request, f"❌ Cannot cancel interview with status: {interview.status}")
        return redirect('my_interviews')
    
    if interview.scheduled_date < timezone.now() + timedelta(hours=2):
        messages.error(request, "❌ Cannot cancel with less than 2 hours notice.")
        return redirect('my_interviews')
    
    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '').strip()
        
        if not cancellation_reason:
            messages.error(request, "❌ Cancellation reason is required.")
            return redirect('interview_detail', interview_id=interview_id)
        
        interview.status = 'cancelled'
        interview.cancellation_reason = cancellation_reason
        interview.cancelled_by = 'candidate'
        interview.cancelled_at = timezone.now()
        interview.save()
        
        messages.success(request, "✅ Interview cancelled successfully.")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Interview cancelled successfully',
                'redirect': reverse('my_interviews')
            })
            
        return redirect('my_interviews')
    
    return redirect('interview_detail', interview_id=interview_id)

# ==================== SAVED JOBS ====================
@login_required
@job_seeker_required
def saved_jobs(request):
    """View saved jobs"""
    saved_jobs_qs = SavedJob.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('job', 'job__company').order_by('-saved_at')
    
    today = timezone.now().date()
    
    saved_jobs_list = []
    applied_count = 0
    not_applied_count = 0
    remote_count = 0
    
    for saved_job in saved_jobs_qs:
        has_applied = Application.objects.filter(
            candidate=request.user,
            job=saved_job.job
        ).exists()
        
        # Count applied and not applied
        if has_applied:
            applied_count += 1
        else:
            not_applied_count += 1
        
        # Count remote jobs
        if saved_job.job.is_remote:
            remote_count += 1
        
        is_expired = False
        if saved_job.job.application_deadline:
            is_expired = saved_job.job.application_deadline < today
        
        saved_jobs_list.append({
            'saved_job': saved_job,
            'job': saved_job.job,
            'saved_date': saved_job.saved_at,
            'notes': saved_job.notes,
            'has_applied': has_applied,
            'is_expired': is_expired,
        })
    
    context = {
        'saved_jobs': saved_jobs_list,
        'today': today,
        'total_count': len(saved_jobs_list),
        'applied_count': applied_count,
        'not_applied_count': not_applied_count,
        'remote_count': remote_count,
    }
    return render(request, 'dashboard/job_seeker/saved_jobs.html', context)

# ==================== SAVE/UNSAVE JOB ====================
@login_required
@job_seeker_required
def save_job(request, job_id):
    """Save or unsave a job"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method.'
        }, status=405)
    
    try:
        job = Job.objects.get(id=job_id, is_active=True, is_approved=True)
    except Job.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Job not found'
        }, status=404)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        action = data.get('action', 'save')
        
        if action == 'save':
            saved_job, created = SavedJob.objects.get_or_create(
                user=request.user,
                job=job,
                defaults={'is_active': True}
            )
            
            if not created and not saved_job.is_active:
                saved_job.is_active = True
                saved_job.save()
            
            return JsonResponse({
                'success': True,
                'action': 'save',
                'message': '✅ Job saved to favorites!',
                'job_id': job_id,
                'is_saved': True
            })
                
        elif action == 'unsave':
            saved_jobs = SavedJob.objects.filter(
                user=request.user,
                job=job,
                is_active=True
            )
            
            if saved_jobs.exists():
                saved_jobs.update(is_active=False)
                return JsonResponse({
                    'success': True,
                    'action': 'unsave',
                    'message': '🗑️ Job removed from favorites',
                    'job_id': job_id,
                    'is_saved': False
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Job not found in saved list'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

# ==================== WITHDRAW APPLICATION ====================
@login_required
@job_seeker_required
def withdraw_application(request, application_id):
    """Withdraw a job application"""
    application = get_object_or_404(Application, id=application_id, candidate=request.user)
    
    if application.status not in ['applied', 'shortlisted']:
        messages.error(request, f"Cannot withdraw application with status: {application.status}")
        return redirect('my_applications')
    
    has_interview = Interview.objects.filter(
        application=application,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).exists()
    
    if has_interview:
        messages.error(request, "Cannot withdraw application with scheduled interview.")
        return redirect('my_applications')
    
    application.status = 'withdrawn'
    application.withdrawn_at = timezone.now()
    application.save()
    
    messages.success(request, "✅ Application withdrawn successfully.")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Application withdrawn successfully',
            'redirect': reverse('my_applications')
        })
    
    return redirect('my_applications')

# ==================== DELETE ACCOUNT ====================
@login_required
@job_seeker_required
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '')
        if confirmation != 'DELETE':
            messages.error(request, "❌ Please type DELETE to confirm.")
            return redirect('delete_account')
        
        user = request.user
        user.delete()
        messages.success(request, "✅ Your account has been deleted.")
        return redirect('homepage')
    
    return render(request, 'dashboard/job_seeker/delete_account.html')

# ==================== UPDATE PROFILE PICTURE ====================
@login_required
@job_seeker_required
def update_profile_picture(request):
    """Update profile picture via AJAX"""
    if request.method == 'POST' and 'profile_picture' in request.FILES:
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile_picture = request.FILES['profile_picture']
            
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "❌ Image size must be less than 5MB")
                return redirect('edit_job_seeker_profile')
            
            profile.profile_picture = profile_picture
            profile.save()
            
            messages.success(request, "✅ Profile picture updated!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Profile picture updated!',
                    'picture_url': profile.profile_picture.url if profile.profile_picture else ''
                })
                
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect('edit_job_seeker_profile')

# ==================== MY MESSAGES ====================
@login_required
@job_seeker_required
def my_messages(request):
    """View all messages/conversations"""
    conversation_id = request.GET.get('conversation')
    
    # Get all messages for this user
    all_messages = Message.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user)
    ).select_related(
        'sender', 
        'recipient'
    ).order_by('-sent_at')
    
    # Get all applications to find companies
    applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job__company')
    
    # Build company mapping
    company_user_map = {}
    for app in applications:
        if app.job and app.job.company:
            company = app.job.company
            # Try different possible relations
            if hasattr(company, 'user') and company.user:
                company_user_map[company.user.id] = company
            elif hasattr(company, 'company_profile') and hasattr(company.company_profile, 'user'):
                company_user_map[company.company_profile.user.id] = company
            elif hasattr(company, 'profile') and hasattr(company.profile, 'user'):
                company_user_map[company.profile.user.id] = company
    
    # Build conversations dictionary
    conversations_dict = {}
    
    # Process each message to build conversations
    for msg in all_messages:
        # Determine the other participant
        other_user = msg.sender if msg.sender != request.user else msg.recipient
        
        if other_user and other_user.id not in conversations_dict:
            # Find company info
            company = company_user_map.get(other_user.id)
            
            # Get all messages for this conversation
            conversation_messages = Message.objects.filter(
                Q(sender=request.user, recipient=other_user) |
                Q(sender=other_user, recipient=request.user)
            ).order_by('sent_at')
            
            # Count unread messages
            unread_count = conversation_messages.filter(
                sender=other_user,
                recipient=request.user,
                is_read=False
            ).count()
            
            # Get company details safely
            company_name = other_user.get_full_name() or other_user.username
            company_logo = None
            company_id = other_user.id
            is_verified = False
            job = None
            
            if company:
                company_name = getattr(company, 'name', company_name)
                company_logo = getattr(company, 'logo', None)
                company_id = getattr(company, 'id', other_user.id)
                is_verified = getattr(company, 'is_verified', False)
                
                # Find job
                user_app = applications.filter(job__company=company).first()
                if user_app:
                    job = user_app.job
            
            conversations_dict[other_user.id] = {
                'id': other_user.id,
                'with_company': {
                    'id': company_id,
                    'name': company_name,
                    'logo': company_logo,
                    'is_verified': is_verified,
                },
                'job': job,
                'last_message': msg,
                'unread_count': unread_count,
                'messages': conversation_messages,
            }
    
    # Sort conversations by last message date
    conversations = sorted(
        conversations_dict.values(),
        key=lambda x: x['last_message'].sent_at if x['last_message'] else datetime.min,
        reverse=True
    )
    
    # Handle active conversation
    active_conversation = None
    if conversation_id and conversation_id.isdigit():
        conv_id = int(conversation_id)
        if conv_id in conversations_dict:
            active_conversation = conversations_dict[conv_id]
            
            # Mark messages as read
            Message.objects.filter(
                sender_id=conv_id,
                recipient=request.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
            active_conversation['unread_count'] = 0
    
    # Calculate total unread
    total_unread = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Slice conversations
    conversations = conversations[:50]
    
    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'total_unread': total_unread,
    }
    return render(request, 'dashboard/job_seeker/messages.html', context)

# ==================== GET CONVERSATION ====================
@login_required
@job_seeker_required
def get_conversation(request, conversation_id):
    """Get conversation messages via AJAX"""
    try:
        user_id = int(conversation_id)
        user = User.objects.get(id=user_id)
        
        messages_qs = Message.objects.filter(
            Q(sender=request.user, recipient=user) |
            Q(sender=user, recipient=request.user)
        ).order_by('sent_at')[:100]
        
        # Mark messages as read
        unread_messages = messages_qs.filter(
            recipient=request.user,
            is_read=False
        )
        unread_messages.update(is_read=True, read_at=timezone.now())
        
        messages_data = []
        for msg in messages_qs:
            messages_data.append({
                'id': msg.id,
                'sender': msg.sender.id,
                'sender_name': msg.sender.get_full_name() or msg.sender.username,
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read,
            })
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation_id,
            'messages': messages_data,
            'timestamp': timezone.now().isoformat()
        })
    except (User.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ==================== SEND MESSAGE ====================
@login_required
@job_seeker_required
def send_message(request):
    """Send a message to a company"""
    recipient_id = request.GET.get('recipient') or request.POST.get('recipient')
    
    # Get companies the user has applied to
    applications = Application.objects.filter(candidate=request.user).select_related('job__company')[:50]
    companies_data = []
    company_ids = set()
    
    for app in applications:
        if hasattr(app.job, 'company') and app.job.company:
            company = app.job.company
            # Try to get the user associated with the company
            company_user = None
            if hasattr(company, 'user') and company.user:
                company_user = company.user
            elif hasattr(company, 'company_profile') and hasattr(company.company_profile, 'user'):
                company_user = company.company_profile.user
            elif hasattr(company, 'profile') and hasattr(company.profile, 'user'):
                company_user = company.profile.user
            
            if company_user and company_user.id not in company_ids:
                companies_data.append({
                    'user': company_user,
                    'company_name': company.name,
                    'company_id': company.id,
                })
                company_ids.add(company_user.id)
    
    # Handle form submission
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient') or request.POST.get('recipient_select')
        content = request.POST.get('content', '').strip()
        subject = request.POST.get('subject', '').strip()
        
        if not recipient_id:
            messages.error(request, "❌ Please select a recipient.")
        elif not content:
            messages.error(request, "❌ Message content cannot be empty.")
        else:
            try:
                recipient_id = int(recipient_id)
                recipient = User.objects.get(id=recipient_id)
                
                message = Message.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=subject,
                    content=content,
                    sent_at=timezone.now(),
                    is_read=False
                )
                
                messages.success(request, "✅ Message sent successfully!")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Message sent successfully!',
                        'message_id': message.id
                    })
                    
                return redirect(f'/job-seeker/my-messages/?conversation={recipient.id}')
                    
            except (User.DoesNotExist, ValueError):
                messages.error(request, "❌ Recipient not found.")
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")
    
    # Check if we have a pre-selected recipient
    selected_company = None
    if recipient_id:
        try:
            recipient_user = User.objects.get(id=int(recipient_id))
            # Find company info for this user
            for company_data in companies_data:
                if company_data['user'].id == recipient_user.id:
                    selected_company = {
                        'id': company_data['company_id'],
                        'name': company_data['company_name'],
                        'logo': None,
                    }
                    break
        except:
            pass
    
    context = {
        'companies': companies_data,
        'recipient_id': recipient_id,
        'selected_company': selected_company,
        'prefilled_subject': request.GET.get('subject', ''),
        'prefilled_content': request.GET.get('content', ''),
    }
    return render(request, 'dashboard/job_seeker/send_message.html', context)

# ==================== START CONVERSATION ====================
@login_required
@job_seeker_required
def start_conversation(request):
    """Alias for send_message"""
    return send_message(request)

# ==================== MARK ALL READ ====================
@login_required
@job_seeker_required
def mark_all_read(request):
    """Mark all messages as read"""
    try:
        unread_count = Message.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        messages.success(request, f"✅ Marked {unread_count} messages as read")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Marked {unread_count} messages as read'
            })
            
        return redirect('my_messages')
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
        return redirect('my_messages')

# ==================== MESSAGE UPDATES ====================
@login_required
@job_seeker_required
def message_updates(request):
    """Get new message updates via AJAX"""
    since = request.GET.get('since', timezone.now().isoformat())
    
    try:
        since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
    except:
        since_date = timezone.now() - timedelta(hours=24)
    
    new_messages = Message.objects.filter(
        recipient=request.user,
        sent_at__gt=since_date,
        is_read=False
    ).select_related('sender')[:50]
    
    updates = []
    for msg in new_messages:
        updates.append({
            'id': msg.id,
            'conversation_id': msg.sender.id,
            'content': msg.content[:100],
            'sent_at': msg.sent_at.isoformat(),
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
        })
    
    return JsonResponse({
        'success': True,
        'updates': updates,
        'count': len(updates),
        'timestamp': timezone.now().isoformat()
    })

# ==================== ANALYTICS ====================
@login_required
@job_seeker_required
def job_seeker_analytics(request):
    """View job seeker analytics with interview tracking"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile.")
        return redirect('edit_job_seeker_profile')
    
    # Get all applications
    applications = Application.objects.filter(candidate=request.user)
    total_applications = applications.count()
    
    # Status counts
    applied_count = applications.filter(status='applied').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    interview_count = applications.filter(status='interview').count()
    selected_count = applications.filter(status='selected').count()
    rejected_count = applications.filter(status='rejected').count()
    
    # Calculate success rate
    success_rate = 0
    if total_applications > 0:
        success_rate = (selected_count / total_applications) * 100
    
    # Calculate interview rate
    interview_rate = 0
    if total_applications > 0:
        interview_rate = ((shortlisted_count + interview_count) / total_applications) * 100
    
    # Get interviews
    interviews = Interview.objects.filter(application__candidate=request.user)
    total_interviews = interviews.count()
    upcoming_interviews = interviews.filter(
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    completed_interviews = interviews.filter(status='completed').count()
    
    # Status data for charts
    status_data = {
        'applied': applied_count,
        'shortlisted': shortlisted_count,
        'interview': interview_count,
        'selected': selected_count,
        'rejected': rejected_count,
    }
    
    # Monthly data for chart (last 6 months)
    monthly_data = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        month = today - timedelta(days=30*i)
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month_start.replace(year=month.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month.month+1, day=1) - timedelta(days=1)
        
        month_apps = applications.filter(
            applied_on__date__gte=month_start,
            applied_on__date__lte=month_end
        ).count()
        
        monthly_data.append({
            'label': month.strftime('%b'),
            'count': month_apps
        })
    
    # Recent applications for table
    recent_applications = applications.select_related(
        'job', 'job__company'
    ).order_by('-applied_on')[:10]
    
    context = {
        'profile': profile,
        'total_applications': total_applications,
        'status_data': status_data,
        'applied_count': applied_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'success_rate': success_rate,
        'interview_rate': interview_rate,
        'total_interviews': total_interviews,
        'upcoming_interviews': upcoming_interviews,
        'completed_interviews': completed_interviews,
        'monthly_data': monthly_data,
        'applications': recent_applications,
    }
    return render(request, 'dashboard/job_seeker/analytics.html', context)

# ==================== DOWNLOAD RESUME ====================
@login_required
@job_seeker_required
def download_resume(request):
    """Download user's resume"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.resume and profile.resume.url:
            return redirect(profile.resume.url)
        messages.error(request, "❌ No resume found.")
    except UserProfile.DoesNotExist:
        messages.error(request, "❌ Profile not found.")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect('edit_job_seeker_profile')

# ==================== SUBSCRIBE JOB ALERTS ====================
@login_required
@job_seeker_required
def subscribe_job_alerts(request):
    """Subscribe to job alerts"""
    if request.method == 'POST':
        search_name = request.POST.get('search_name', '').strip()
        if not search_name:
            messages.error(request, "❌ Search name is required")
            return redirect('search_jobs')
        
        messages.success(request, f"✅ Job alert '{search_name}' created successfully!")
        redirect_url = f"{request.path}?{request.GET.urlencode()}"
        return redirect(redirect_url)
    
    return redirect('search_jobs')

# ==================== TEST AJAX ====================
@login_required
def test_ajax(request):
    """Test AJAX functionality"""
    return JsonResponse({
        'success': True,
        'message': '✅ AJAX is working!',
        'user': request.user.username,
        'timestamp': timezone.now().isoformat()
    })

# ==================== SAVED JOBS COUNT ====================
@login_required
def saved_jobs_count(request):
    """Get saved jobs count via AJAX"""
    try:
        count = SavedJob.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'count': 0
        })

# ==================== GET DASHBOARD STATS ====================
@login_required
def get_dashboard_stats(request):
    """Get dashboard stats via AJAX"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    total_applications = Application.objects.filter(candidate=request.user).count()
    pending_applications = Application.objects.filter(
        candidate=request.user, 
        status__in=['applied', 'shortlisted']
    ).count()
    
    upcoming_interviews = Interview.objects.filter(
        application__candidate=request.user,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    
    unread_messages = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    saved_jobs_count = SavedJob.objects.filter(user=request.user, is_active=True).count()
    
    profile_completion = calculate_profile_completion(profile)
    
    return JsonResponse({
        'success': True,
        'stats': {
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'upcoming_interviews': upcoming_interviews,
            'unread_messages': unread_messages,
            'saved_jobs_count': saved_jobs_count,
            'profile_completion': profile_completion,
        },
        'timestamp': timezone.now().isoformat()
    })

# ==================== QUICK APPLY ====================
@login_required
@job_seeker_required
def quick_apply(request, job_id):
    """Quick apply for a job via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    try:
        job = Job.objects.get(id=job_id, is_active=True, is_approved=True)
        
        if Application.objects.filter(job=job, candidate=request.user).exists():
            return JsonResponse({
                'success': False,
                'error': 'Already applied'
            })
        
        today = timezone.now().date()
        if job.application_deadline and job.application_deadline < today:
            return JsonResponse({
                'success': False,
                'error': 'Deadline passed'
            })
        
        try:
            profile = UserProfile.objects.get(user=request.user)
            resume = profile.resume
        except UserProfile.DoesNotExist:
            resume = None
        
        if not resume:
            return JsonResponse({
                'success': False,
                'error': 'Please upload resume first'
            })
        
        application = Application.objects.create(
            job=job,
            candidate=request.user,
            cover_letter=f"Applying for {job.title} position at {job.company.name}. I am interested in this opportunity and believe my skills match the requirements.",
            resume=resume,
            status='applied',
            applied_on=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'application_id': application.id,
            'message': '✅ Application submitted successfully!'
        })
        
    except Job.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== VALIDATE RESUME ====================
@login_required
@job_seeker_required
@require_POST
@csrf_exempt
def validate_resume(request):
    """Validate resume before applying"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        if not profile.resume:
            return JsonResponse({
                'has_resume': False,
                'message': '❌ Please upload your resume before applying for jobs.',
                'redirect': reverse('edit_job_seeker_profile')
            })
        
        return JsonResponse({
            'has_resume': True,
            'message': '✅ Resume found!',
            'resume_url': profile.resume.url if profile.resume else ''
        })
            
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'has_resume': False,
            'message': '❌ Please complete your profile first.',
            'redirect': reverse('edit_job_seeker_profile')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'has_resume': False,
            'message': f'❌ Error: {str(e)}',
            'redirect': reverse('edit_job_seeker_profile')
        }, status=500)

# ==================== DELETE MESSAGES ====================
@login_required
@job_seeker_required
def delete_message(request):
    """Delete a specific message received from company"""
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            import json
            data = json.loads(request.body)
            message_id = data.get('message_id')
        
        try:
            # Ensure user can only delete messages they received
            message = Message.objects.get(id=message_id, recipient=request.user)
            message.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Message deleted successfully'})
            
            messages.success(request, 'Message deleted successfully')
            return redirect(request.META.get('HTTP_REFERER', 'my_messages'))
            
        except Message.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
            
            messages.error(request, 'Message not found')
            return redirect('my_messages')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Error: {str(e)}')
            return redirect('my_messages')
    
    return redirect('my_messages')


@login_required
@job_seeker_required
def delete_conversation(request):
    """Delete an entire conversation"""
    if request.method == 'POST':
        conversation_id = request.POST.get('conversation_id')
        
        try:
            other_user_id = int(conversation_id)
            # Delete all messages between user and the other participant
            deleted_count = Message.objects.filter(
                Q(sender=request.user, recipient_id=other_user_id) |
                Q(sender_id=other_user_id, recipient=request.user)
            ).delete()
            
            messages.success(request, f'Conversation deleted successfully')
            return redirect('my_messages')
            
        except ValueError:
            messages.error(request, 'Invalid conversation ID')
            return redirect('my_messages')
        except Exception as e:
            messages.error(request, f'Error deleting conversation: {str(e)}')
            return redirect('my_messages')
    
    return redirect('my_messages')