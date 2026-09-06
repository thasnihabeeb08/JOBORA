from django.shortcuts import redirect
from django.contrib import messages
from jobs.models import Company

def company_active_required(view_func):
    """Check if company is approved and active"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('login')
        
        # Check if user is blocked by admin
        if not request.user.is_active:
            messages.error(request, "Your account has been suspended. Contact admin.")
            return redirect('login')
        
        # Check if company exists and is approved
        try:
            company = Company.objects.get(user=request.user)
            if not company.is_approved:
                messages.error(request, "Your company is pending approval. Please wait for admin verification.")
                return redirect('company_dashboard')
        except Company.DoesNotExist:
            messages.error(request, "Company profile not found.")
            return redirect('register_company')
        
        return view_func(request, *args, **kwargs)
    return wrapper