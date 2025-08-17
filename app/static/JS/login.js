function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    if (input.type === "password") {
        input.type = "text";
        btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        input.type = "password";
        btn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Initialize password toggle icons when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.innerHTML = '<i class="fas fa-eye"></i>';
    });
    
    // Add animation class to form wrapper after a slight delay
    setTimeout(() => {
        const formWrapper = document.querySelector('.auth-form-wrapper');
        if (formWrapper) {
            formWrapper.classList.add('animated');
        }
    }, 100);
});