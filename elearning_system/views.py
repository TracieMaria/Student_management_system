"""
Custom views for handling system errors
"""
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def csrf_failure(request, reason=""):
    """
    Custom view to handle CSRF failures with a more user-friendly message.
    """
    # Log CSRF failure for debugging
    logger.error(f"CSRF Failure: {reason}. Headers: {dict(request.headers)}")
    
    # Check if CSRF cookie exists
    has_cookie = 'csrftoken' in request.COOKIES
    
    context = {
        'reason': reason,
        'has_cookie': has_cookie,
        'request_method': request.method,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'referer': request.headers.get('Referer', 'None'),
        'csrf_token': request.COOKIES.get('csrftoken', 'Not found'),
    }
    
    return render(request, 'csrf_failure.html', context)
