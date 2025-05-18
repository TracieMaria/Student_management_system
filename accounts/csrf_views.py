"""
Custom CSRF views to handle CSRF errors in a user-friendly way.
"""
from django.shortcuts import render
from django.middleware.csrf import get_token

def csrf_failure(request, reason="", template_name="csrf_failure.html"):
    """
    Custom view for CSRF failures with more helpful error details and possible fixes.
    """
    # Generate a fresh CSRF token
    csrf_token = get_token(request)
    
    context = {
        'reason': reason,
        'csrf_token': csrf_token,
        'has_cookie': request.COOKIES.get('csrftoken', None) is not None,
        'request_method': request.method,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'referer': request.headers.get('Referer', 'None'),
    }
    
    return render(request, template_name, context)
