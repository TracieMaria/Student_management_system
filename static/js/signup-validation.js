// Signup form validation and CSRF token handling
document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signup-form');
    const csrfDebug = document.getElementById('csrf-debug');
    const csrfStatus = document.getElementById('csrf-status');
    const submitBtn = document.getElementById('signup-submit-btn');
    const submitText = document.getElementById('submit-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const csrfError = document.getElementById('csrf-error');
    
    // For debugging purposes - uncomment to show the CSRF debug panel
    if (csrfDebug) {
        csrfDebug.classList.remove('hidden');
    }
    
    // Function to get cookie by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Function to refresh the CSRF token
    function refreshCsrfToken() {
        console.log('Attempting to refresh CSRF token...');
        
        // Make a GET request to the current page to get a fresh CSRF token
        fetch(window.location.href, {
            method: 'GET',
            credentials: 'same-origin',
            cache: 'no-store' // Ensure we don't use a cached response
        })
        .then(response => {
            // Check for and store any CSRF cookie that was set
            const setCookieHeader = response.headers.get('Set-Cookie');
            if (setCookieHeader) {
                console.log('Set-Cookie header received:', setCookieHeader.includes('csrftoken') ? 'Contains csrftoken' : 'No csrftoken found');
            }
            return response.text();
        })
        .then(html => {
            // Parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Find the CSRF token in the response
            const newCsrfToken = doc.querySelector('input[name="csrfmiddlewaretoken"]');
            
            if (newCsrfToken && newCsrfToken.value) {
                // Replace the current CSRF token with the new one
                const currentToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
                if (currentToken) {
                    currentToken.value = newCsrfToken.value;
                    console.log('CSRF token refreshed successfully:', newCsrfToken.value.substring(0, 10) + '...');
                    
                    if (csrfStatus) {
                        csrfStatus.textContent = 'Refreshed';
                        csrfStatus.style.color = 'green';
                    }
                    
                    if (csrfError) {
                        csrfError.classList.add('hidden');
                    }
                    
                    // Add csrf token as a hidden field again to be double sure
                    const hiddenField = document.createElement('input');
                    hiddenField.type = 'hidden';
                    hiddenField.name = 'csrfmiddlewaretoken';
                    hiddenField.value = newCsrfToken.value;
                    
                    // Replace any existing hidden field with the same name
                    const existingHiddenField = signupForm.querySelector('input[name="csrfmiddlewaretoken"]');
                    if (existingHiddenField) {
                        signupForm.replaceChild(hiddenField, existingHiddenField);
                    } else {
                        signupForm.prepend(hiddenField);
                    }
                }
            } else {
                console.error('Could not find new CSRF token in response');
                if (csrfStatus) {
                    csrfStatus.textContent = 'Error refreshing';
                    csrfStatus.style.color = 'red';
                }
            }
        })
        .catch(error => {
            console.error('Error refreshing CSRF token:', error);
        });
    }
    
    // Check if CSRF debug is enabled and update status
    if (csrfStatus) {
        const csrftoken = getCookie('csrftoken');
        csrfStatus.textContent = csrftoken ? 'Available' : 'Not found';
        csrfStatus.style.color = csrftoken ? 'green' : 'red';
        
        if (!csrftoken) {
            // Try to refresh the token if not found
            refreshCsrfToken();
        }
    }
    
    // Add form submission handler if the form exists
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            // Show loading state
            if (submitBtn && loadingSpinner && submitText) {
                submitBtn.disabled = true;
                submitText.textContent = 'Creating Account...';
                loadingSpinner.classList.remove('hidden');
            }
            
            // Check for CSRF token presence
            const csrfInput = signupForm.querySelector('input[name="csrfmiddlewaretoken"]');
            if (!csrfInput || !csrfInput.value) {
                e.preventDefault();
                console.error('CSRF token missing in the form');
                
                // Show error message to user
                if (csrfError) {
                    csrfError.classList.remove('hidden');
                }
                
                // Reset button state
                if (submitBtn && loadingSpinner && submitText) {
                    submitBtn.disabled = false;
                    submitText.textContent = 'Create Account';
                    loadingSpinner.classList.add('hidden');
                }
                
                // Try to refresh the CSRF token
                refreshCsrfToken();
                
                return;
            }
            
            // Form is good to go, will submit normally
            console.log('Form submission with CSRF token: ', csrfInput.value.substring(0, 5) + '...');
        });
    }
    
    // Add a refresh token button if debug is enabled
    if (csrfDebug && csrfStatus) {
        const refreshButton = document.createElement('button');
        refreshButton.textContent = 'Refresh Token';
        refreshButton.className = 'text-xs text-blue-500 underline ml-2';
        refreshButton.addEventListener('click', function(e) {
            e.preventDefault();
            refreshCsrfToken();
        });
        
        csrfDebug.appendChild(refreshButton);
    }
});
