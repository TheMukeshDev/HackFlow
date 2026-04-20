// HackFlow Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm before leaving if form has unsaved changes
    const forms = document.querySelectorAll('form[data-confirm]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Queue refresh every 30 seconds on queue page
    if (document.querySelector('.queue-page')) {
        setInterval(function() {
            location.reload();
        }, 30000);
    }

    // Toggle password visibility
    const passwordToggles = document.querySelectorAll('.toggle-password');
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const input = document.querySelector(toggle.dataset.target);
            if (input.type === 'password') {
                input.type = 'text';
                toggle.classList.remove('bi-eye-slash');
                toggle.classList.add('bi-eye');
            } else {
                input.type = 'password';
                toggle.classList.remove('bi-eye');
                toggle.classList.add('bi-eye-slash');
            }
        });
    });
});

// CSRF token helper for AJAX requests
function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// AJAX helper
function ajax(url, options) {
    options = options || {};
    options.headers = options.headers || {};
    options.headers['X-CSRF-Token'] = csrfToken();
    
    return fetch(url, options).then(function(response) {
        if (!response.ok) {
            throw new Error('Network error: ' + response.status);
        }
        return response.json();
    });
}