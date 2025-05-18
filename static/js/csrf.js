// CSRF Token handling for AJAX requests
document.addEventListener('DOMContentLoaded', function() {
    // Function to get cookie by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Get the CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // Set up AJAX requests to include the CSRF token
    if (window.fetch) {
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            options = options || {};
            
            if (options.method && options.method.toUpperCase() !== 'GET') {
                if (!options.headers) {
                    options.headers = {};
                }
                
                // Only add the header if it's not already set
                if (!options.headers['X-CSRFToken'] && !options.headers['x-csrftoken']) {
                    options.headers['X-CSRFToken'] = csrftoken;
                }
            }
            
            return originalFetch.call(this, url, options);
        };
    }
    
    // For XMLHttpRequest
    const originalOpen = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function() {
        const result = originalOpen.apply(this, arguments);
        const method = arguments[0];
        
        if (method.toUpperCase() !== 'GET') {
            this.addEventListener('loadstart', function() {
                if (!this.getResponseHeader('X-CSRFToken') && !this.getResponseHeader('x-csrftoken')) {
                    this.setRequestHeader('X-CSRFToken', csrftoken);
                }
            });
        }
        
        return result;
    };

    // Log if CSRF token exists
    console.log('CSRF token available:', csrftoken ? 'Yes' : 'No');
});
