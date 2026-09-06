from django.shortcuts import redirect
from django.contrib import messages
from users.models import UserProfile

def job_seeker_required(view_func):
    """Check if user has a job seeker profile and is active"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('login_job_seeker')
        
        # Check if user is blocked by admin
        if not request.user.is_active:
            messages.error(request, "Your account has been suspended. Contact admin.")
            return redirect('login_job_seeker')
        
        # Check if user has a job seeker profile
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "Please complete your job seeker profile first.")
            return redirect('edit_job_seeker_profile')
        
        return view_func(request, *args, **kwargs)
    return wrapper