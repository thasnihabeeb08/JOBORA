from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
import random
import string

# Import forms
from .forms import CompanyRegistrationForm, JobSeekerRegistrationForm

# Import models
from .models import Company, UserProfile

# Try importing Job and Application from jobs app
try:
    from jobs.models import Job, Application
    HAVE_JOBS_MODELS = True
except ImportError:
    HAVE_JOBS_MODELS = False
    Job = None
    Application = None

# ========== COMPANY REGISTRATION ==========

def register_company(request):
    """Company registration view"""
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Company account created successfully!')
            return redirect('homepage')
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'accounts/register_company.html', {'form': form})

# ========== JOB SEEKER REGISTRATION ==========

def register_job_seeker(request):
    """Job Seeker Registration View"""
    if request.method == 'POST':
        form = JobSeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Job Seeker account created successfully!')
            return redirect('homepage')
    else:
        form = JobSeekerRegistrationForm()
    
    return render(request, 'accounts/register_job_seeker.html', {'form': form})

# ========== LOGIN VIEWS ==========

def user_login(request):
    """Universal login view - redirects based on user type"""
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not identifier or not password:
            messages.error(request, 'Please enter both email/username and password.')
            return render(request, 'accounts/login.html')
        
        user = None
        
        # Try to find user by email
        try:
            user_by_email = User.objects.get(email__iexact=identifier)
            user = authenticate(request, username=user_by_email.username, password=password)
        except User.DoesNotExist:
            pass
        
        # If not found by email, try with username
        if user is None:
            user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            # CHECK IF USER IS BLOCKED
            if not user.is_active:
                messages.error(request, 'Your account has been blocked. Please contact administrator for assistance.')
                return render(request, 'accounts/login.html')
            
            login(request, user)
            messages.success(request, 'Login successful!')
            
            # Check if user has company profile
            try:
                Company.objects.get(user=user)
                return redirect('company_dashboard')
            except Company.DoesNotExist:
                # Check if user has job seeker profile
                try:
                    UserProfile.objects.get(user=user)
                    return redirect('job_seeker_dashboard')
                except UserProfile.DoesNotExist:
                    # If no profile exists, redirect to create profile
                    return redirect('create_profile')
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    return render(request, 'accounts/login.html')

def login_job_seeker(request):
    """Job Seeker specific login - shows job seeker themed login"""
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not identifier or not password:
            messages.error(request, 'Please enter both email/username and password.')
            return render(request, 'accounts/login_job_seeker.html')
        
        # FIRST: Check if user exists
        try:
            # Try to find user by email first
            try:
                user_obj = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                # If not found by email, try by username
                user_obj = User.objects.get(username=identifier)
            
            # If user exists but is blocked, show blocked message
            if not user_obj.is_active:
                messages.error(request, 'Your account has been blocked. Please contact administrator for assistance.')
                return render(request, 'accounts/login_job_seeker.html')
                
        except User.DoesNotExist:
            # User doesn't exist - will show invalid credentials after authentication
            user_obj = None
        
        # THEN: Try to authenticate
        user = authenticate(request, username=identifier, password=password)
        
        # If authentication failed but user exists, we already checked if blocked
        if user is None and user_obj is not None:
            messages.error(request, 'Invalid password.')
            return render(request, 'accounts/login_job_seeker.html')
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            
            # Check user type and redirect appropriately
            try:
                Company.objects.get(user=user)
                return redirect('company_dashboard')
            except Company.DoesNotExist:
                try:
                    UserProfile.objects.get(user=user)
                    return redirect('job_seeker_dashboard')
                except UserProfile.DoesNotExist:
                    return redirect('create_profile')
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    return render(request, 'accounts/login_job_seeker.html')
def login_company(request):
    """Company specific login view"""
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Clear any existing messages
        storage = messages.get_messages(request)
        storage.used = True
        
        if not identifier or not password:
            messages.error(request, 'Please enter both email/username and password.')
            return redirect('login_company')
        
        # Try to find user by email first
        user_obj = None
        try:
            # Try email first
            user_obj = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            try:
                # If not found by email, try username
                user_obj = User.objects.get(username=identifier)
            except User.DoesNotExist:
                user_obj = None
        
        # If user exists but is blocked
        if user_obj and not user_obj.is_active:
            messages.error(request, 'Your company account has been suspended. Please contact administrator.')
            return redirect('login_company')
        
        # Authenticate - try with username
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            # Check if company exists and is approved
            try:
                company = Company.objects.get(user=user)
                if not company.is_approved:
                    messages.error(request, 'Your company is pending approval. Please wait for admin verification.')
                    return redirect('login_company')
            except Company.DoesNotExist:
                messages.error(request, 'Company profile not found.')
                return redirect('login_company')
            
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('company_dashboard')
        else:
            if user_obj is not None:
                messages.error(request, 'Invalid password.')
            else:
                messages.error(request, 'Invalid email/username or password.')
            return redirect('login_company')
    
    return render(request, 'accounts/login.html')

# ========== LOGOUT ==========

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('homepage')

# ========== PASSWORD RESET ==========

def forgot_password(request):
    """Forgot password view - Step 1: Email input"""
    if 'reset_data' in request.session:
        del request.session['reset_data']
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/forgot_password.html', {'step': 1})
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'accounts/forgot_password.html', {'step': 1})
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            
            # Check if user is blocked
            if not user.is_active:
                messages.error(request, 'This account has been blocked. Cannot reset password. Please contact administrator.')
                return render(request, 'accounts/forgot_password.html', {'step': 1})
                
        except User.DoesNotExist:
            # Still proceed but will show error at reset step
            pass
        
        otp = ''.join(random.choices(string.digits, k=6))
        
        reset_data = {
            'otp': otp,
            'email': email,
            'created_at': timezone.now().isoformat(),
            'attempts': 0,
            'verified': False
        }
        request.session['reset_data'] = reset_data
        
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - OTP Generated")
            print(f"Email: {email}")
            print(f"OTP: {otp}")
            print(f"{'='*60}\n")
            
            messages.success(request, 'OTP generated successfully!')
            messages.info(request, f'Development Mode: Your OTP is <strong>{otp}</strong>.')
        else:
            try:
                subject = 'Jobora - Password Reset OTP'
                message = f"""Dear User,

Your OTP verification code is: {otp}

This OTP is valid for 10 minutes.

Jobora Team
"""
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, f'OTP has been sent to {email}.')
                
            except Exception as e:
                if 'reset_data' in request.session:
                    del request.session['reset_data']
                
                messages.error(request, f'Failed to send OTP: {str(e)}')
                return render(request, 'accounts/forgot_password.html', {'step': 1})
        
        return render(request, 'accounts/forgot_password.html', {
            'step': 2, 
            'email': email,
            'debug': settings.DEBUG,
            'dev_otp': otp if settings.DEBUG else None
        })
    
    return render(request, 'accounts/forgot_password.html', {
        'step': 1,
        'debug': settings.DEBUG
    })

def verify_otp(request):
    """Forgot password view - Step 2: OTP verification"""
    reset_data = request.session.get('reset_data')
    if not reset_data:
        messages.error(request, 'OTP session expired. Please start again.')
        return redirect('forgot_password')
    
    email = reset_data.get('email')
    
    if request.method == 'POST':
        otp_entered = ''.join([
            request.POST.get('otp1', ''),
            request.POST.get('otp2', ''),
            request.POST.get('otp3', ''),
            request.POST.get('otp4', ''),
            request.POST.get('otp5', ''),
            request.POST.get('otp6', '')
        ])
        
        stored_otp = reset_data.get('otp')
        created_at = reset_data.get('created_at')
        
        if created_at:
            try:
                created_time = timezone.datetime.fromisoformat(created_at)
                if timezone.now() - created_time > timedelta(minutes=10):
                    del request.session['reset_data']
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return redirect('forgot_password')
            except:
                del request.session['reset_data']
                messages.error(request, 'OTP session invalid. Please start again.')
                return redirect('forgot_password')
        
        if not otp_entered or len(otp_entered) != 6:
            messages.error(request, 'Please enter the complete 6-digit OTP.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 2, 
                'email': email,
                'debug': settings.DEBUG
            })
        
        if otp_entered != stored_otp:
            reset_data['attempts'] = reset_data.get('attempts', 0) + 1
            request.session['reset_data'] = reset_data
            
            if reset_data['attempts'] >= 3:
                del request.session['reset_data']
                messages.error(request, 'Too many failed attempts. Please start again.')
                return redirect('forgot_password')
            
            attempts_left = 3 - reset_data['attempts']
            messages.error(request, f'Invalid OTP. {attempts_left} attempt(s) remaining.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 2, 
                'email': email,
                'debug': settings.DEBUG
            })
        
        reset_data['verified'] = True
        reset_data['verified_at'] = timezone.now().isoformat()
        request.session['reset_data'] = reset_data
        
        messages.success(request, 'OTP verified successfully. You can now set your new password.')
        return render(request, 'accounts/forgot_password.html', {
            'step': 3, 
            'email': email,
            'debug': settings.DEBUG
        })
    
    return render(request, 'accounts/forgot_password.html', {
        'step': 2, 
        'email': email,
        'debug': settings.DEBUG
    })

def reset_password(request):
    """Forgot password view - Step 3: Set new password"""
    reset_data = request.session.get('reset_data')
    if not reset_data or not reset_data.get('verified'):
        messages.error(request, 'Please verify OTP first.')
        return redirect('forgot_password')
    
    email = reset_data.get('email')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            messages.error(request, 'Please fill in all password fields.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 3, 
                'email': email,
                'debug': settings.DEBUG
            })
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 3, 
                'email': email,
                'debug': settings.DEBUG
            })
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 3, 
                'email': email,
                'debug': settings.DEBUG
            })
        
        try:
            user = User.objects.get(email=email)
            
            # Double-check user is not blocked
            if not user.is_active:
                messages.error(request, 'Cannot reset password for blocked account. Please contact administrator.')
                return redirect('forgot_password')
            
            user.set_password(new_password)
            user.save()
            
            if not settings.DEBUG:
                try:
                    subject = 'Jobora - Password Changed Successfully'
                    message = f"""Dear {user.username},

Your password has been changed successfully.

Jobora Team
"""
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=True,
                    )
                except:
                    pass
            
            if 'reset_data' in request.session:
                del request.session['reset_data']
            
            messages.success(request, 'Password reset successfully! You can now login with your new password.')
            return render(request, 'accounts/forgot_password.html', {
                'step': 'success',
                'debug': settings.DEBUG
            })
            
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
            return redirect('forgot_password')
        except Exception as e:
            messages.error(request, f'Error resetting password: {str(e)}')
            return render(request, 'accounts/forgot_password.html', {
                'step': 3, 
                'email': email,
                'debug': settings.DEBUG
            })
    
    return render(request, 'accounts/forgot_password.html', {
        'step': 3, 
        'email': email,
        'debug': settings.DEBUG
    })

def resend_otp(request):
    """Resend OTP view"""
    reset_data = request.session.get('reset_data')
    
    if not reset_data:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')
    
    email = reset_data.get('email')
    
    # Check if user exists and is active
    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            messages.error(request, 'This account has been blocked. Cannot reset password.')
            return redirect('forgot_password')
    except User.DoesNotExist:
        # Will be caught at reset step
        pass
    
    # Generate new OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Update reset data
    reset_data['otp'] = otp
    reset_data['created_at'] = timezone.now().isoformat()
    reset_data['attempts'] = 0
    reset_data['verified'] = False
    request.session['reset_data'] = reset_data
    
    # DEVELOPMENT MODE - Show in console
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"RESENT OTP (Development Mode)")
        print(f"Email: {email}")
        print(f"NEW OTP: {otp}")
        print(f"Time: {timezone.now()}")
        print(f"{'='*60}\n")
        
        messages.success(request, 'New OTP generated successfully!')
        messages.info(request, f'Development Mode: Your new OTP is <strong>{otp}</strong>')
    else:
        # PRODUCTION MODE - Send real email
        try:
            subject = 'Jobora - New Password Reset OTP'
            message = f"""Dear User,

You have requested a new OTP for password reset on Jobora.

Your new OTP verification code is: {otp}

This OTP is valid for 10 minutes.

If you didn't request this password reset, please ignore this email.

Best regards,
Jobora Team
"""
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'New OTP has been sent to your email address.')
            
        except Exception as e:
            messages.error(request, f'Failed to resend OTP: {str(e)}')
    
    return render(request, 'accounts/forgot_password.html', {
        'step': 2, 
        'email': email,
        'debug': settings.DEBUG,
        'dev_otp': otp if settings.DEBUG else None
    })

# ========== DASHBOARD VIEWS ==========

@login_required
def company_dashboard(request):
    """Company dashboard view"""
    # Check if user is blocked (redundant but safe)
    if not request.user.is_active:
        logout(request)
        messages.error(request, 'Your account has been blocked. Please contact administrator.')
        return redirect('login')
    
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'No company profile found.')
        return redirect('homepage')
    
    # Calculate stats
    total_jobs = 0
    active_jobs = 0
    total_applications = 0
    
    if HAVE_JOBS_MODELS:
        total_jobs = Job.objects.filter(company=company).count()
        active_jobs = Job.objects.filter(company=company, is_active=True).count()
        total_applications = Application.objects.filter(job__company=company).count()
    
    context = {
        'company': company,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
    }
    return render(request, 'dashboard/company_dashboard.html', context)

@login_required
def job_seeker_dashboard(request):
    """Job Seeker Dashboard View"""
    # Check if user is blocked (redundant but safe)
    if not request.user.is_active:
        logout(request)
        messages.error(request, 'Your account has been blocked. Please contact administrator.')
        return redirect('login_job_seeker')
    
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('create_profile')
    
    # Get stats
    total_applications = 0
    pending_applications = 0
    
    if HAVE_JOBS_MODELS:
        total_applications = Application.objects.filter(candidate=request.user).count()
        pending_applications = Application.objects.filter(
            candidate=request.user, status='applied'
        ).count()
    
    # Get recent applications
    recent_applications = []
    if HAVE_JOBS_MODELS:
        recent_applications = Application.objects.filter(
            candidate=request.user
        ).order_by('-applied_on')[:5]
    
    context = {
        'profile': profile,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'recent_applications': recent_applications,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'dashboard/job_seeker/dashboard.html', context)

# ========== PROFILE MANAGEMENT ==========

@login_required
def create_profile(request):
    """Create or complete job seeker profile"""
    # Check if user is blocked
    if not request.user.is_active:
        logout(request)
        messages.error(request, 'Your account has been blocked. Please contact administrator.')
        return redirect('login_job_seeker')
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        is_edit = True
    except UserProfile.DoesNotExist:
        profile = None
        is_edit = False
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        # Create or update profile
        if not profile:
            profile = UserProfile(user=request.user)
        
        profile.phone = request.POST.get('phone', '')
        profile.location = request.POST.get('location', '')
        profile.user_type = request.POST.get('user_type', 'fresher')
        profile.skills = request.POST.get('skills', '')
        profile.is_profile_complete = True
        profile.save()
        
        messages.success(request, 'Profile saved successfully!')
        return redirect('job_seeker_dashboard')
    
    context = {
        'profile': profile,
        'is_edit': is_edit,
        'user': request.user,
        'user_types': UserProfile.USER_TYPES,
    }
    return render(request, 'dashboard/job_seeker/create_profile.html', context)

# ========== SEARCH FUNCTIONALITY ==========

@login_required
def search_jobs(request):
    """Search jobs for company users"""
    # Check if user is blocked
    if not request.user.is_active:
        logout(request)
        messages.error(request, 'Your account has been blocked. Please contact administrator.')
        return redirect('login')
    
    query = request.GET.get('q', '')
    
    # Get company
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'No company profile found.')
        return redirect('homepage')
    
    # Search jobs
    jobs = []
    if HAVE_JOBS_MODELS:
        jobs = Job.objects.filter(company=company)
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )
    
    context = {
        'jobs': jobs,
        'query': query,
        'total_jobs': len(jobs),
        'company': company,
    }
    return render(request, 'dashboard/search_jobs.html', context)