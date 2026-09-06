# admin_panel/decorators.py
from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def admin_required(view_func):
    """
    Decorator to check if user is admin (superuser or staff)
    Use this on all admin pages to protect them
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is logged in and is admin
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You need admin access to view this page")
            return redirect('admin_login')
    return wrapper