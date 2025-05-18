"""
Context processors for the accounts app.
"""
import logging

logger = logging.getLogger(__name__)

def csrf_settings(request):
    """
    Add CSRF-related settings to the template context.
    This can help ensure CSRF cookies are properly set and respected.
    """
    # Check if CSRF cookie exists in the request
    has_csrf_cookie = 'csrftoken' in request.COOKIES
    
    if not has_csrf_cookie:
        logger.warning(f"CSRF cookie not found in request. Available cookies: {list(request.COOKIES.keys())}")
    
    return {
        'csrf_cookie_secure': request.is_secure(),
        'csrf_cookie_httponly': False,  # Must be False to be accessible by JavaScript if needed
        'csrf_cookie_samesite': 'Lax',  # Default value in Django
        'has_csrf_cookie': has_csrf_cookie,
        'csrf_cookie_name': 'csrftoken',
    }
