// Main JavaScript file for SkyLink Airlines

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initPasswordToggles();
    initSeatSelection();
    initFormValidation();
    initDatePickers();
    initTooltips();
    initModals();
    initCharts();
});

// Password toggle functionality
function initPasswordToggles() {
    const passwordToggles = document.querySelectorAll('.btn-eye');
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordField = document.getElementById(this.getAttribute('data-target'));
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                this.innerHTML = '🙈';
            } else {
                passwordField.type = 'password';
                this.innerHTML = '👁';
            }
        });
    });
}

// Seat selection functionality
function initSeatSelection() {
    const seats = document.querySelectorAll('.seat:not(.booked)');
    const selectedSeats = new Set();
    const maxSeats = parseInt(document.getElementById('max-seats')?.value || 1);
    
    seats.forEach(seat => {
        seat.addEventListener('click', function() {
            const seatId = this.getAttribute('data-seat-id');
            
            if (this.classList.contains('selected')) {
                // Deselect seat
                this.classList.remove('selected');
                selectedSeats.delete(seatId);
            } else {
                // Select seat if under limit
                if (selectedSeats.size < maxSeats) {
                    this.classList.add('selected');
                    selectedSeats.add(seatId);
                } else {
                    showAlert('You can only select ' + maxSeats + ' seat(s)', 'warning');
                }
            }
            
            // Update hidden input
            updateSelectedSeatsInput();
        });
    });
}

function updateSelectedSeatsInput() {
    const selectedSeats = Array.from(document.querySelectorAll('.seat.selected')).map(seat => seat.getAttribute('data-seat-id'));
    const input = document.getElementById('selected-seats');
    if (input) {
        input.value = selectedSeats.join(',');
    }
}

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });
}

function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    const fieldName = field.name;
    
    // Clear previous errors
    clearFieldError(event);
    
    // Validation rules
    let isValid = true;
    let errorMessage = '';
    
    switch (fieldName) {
        case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
            break;
            
        case 'password':
            if (value.length < 6) {
                isValid = false;
                errorMessage = 'Password must be at least 6 characters long';
            }
            break;
            
        case 'confirm_password':
            const password = document.querySelector('input[name="password"]')?.value;
            if (value !== password) {
                isValid = false;
                errorMessage = 'Passwords do not match';
            }
            break;
            
        case 'card_number':
            const cardRegex = /^\d{13,19}$/;
            if (!cardRegex.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Please enter a valid card number';
            }
            break;
            
        case 'cvv':
            const cvvRegex = /^\d{3,4}$/;
            if (!cvvRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid CVV';
            }
            break;
    }
    
    if (!isValid) {
        showFieldError(field, errorMessage);
    }
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(event) {
    const field = event.target;
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Date picker initialization
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        input.setAttribute('min', today);
        
        // Add change event for return date validation
        if (input.name === 'return_date') {
            input.addEventListener('change', function() {
                const departureDate = document.querySelector('input[name="departure_date"]')?.value;
                if (departureDate && this.value <= departureDate) {
                    showAlert('Return date must be after departure date', 'warning');
                    this.value = '';
                }
            });
        }
    });
}

// Tooltip initialization
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Modal initialization
function initModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const modalInstance = new bootstrap.Modal(modal);
        
        // Auto-hide modals after 5 seconds
        modal.addEventListener('shown.bs.modal', function() {
            setTimeout(() => {
                modalInstance.hide();
            }, 5000);
        });
    });
}

// Chart initialization (for admin dashboard)
function initCharts() {
    // Check if Chart.js is available
    if (typeof Chart !== 'undefined') {
        // Revenue chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            const revenueData = JSON.parse(revenueCtx.getAttribute('data-chart'));
            new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: revenueData.labels,
                    datasets: [{
                        label: 'Revenue',
                        data: revenueData.values,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
        
        // Booking class chart
        const classCtx = document.getElementById('classChart');
        if (classCtx) {
            const classData = JSON.parse(classCtx.getAttribute('data-chart'));
            new Chart(classCtx, {
                type: 'doughnut',
                data: {
                    labels: classData.labels,
                    datasets: [{
                        data: classData.values,
                        backgroundColor: [
                            '#3b82f6',
                            '#f59e0b',
                            '#10b981',
                            '#ef4444'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }
    }
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// AJAX utility functions
function makeRequest(url, method = 'GET', data = null) {
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: data ? JSON.stringify(data) : null
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Request failed:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    });
}

// Flight search functionality
function searchFlights() {
    const form = document.getElementById('flight-search-form');
    if (!form) return;
    
    const formData = new FormData(form);
    const searchData = Object.fromEntries(formData.entries());
    
    // Validate required fields
    const requiredFields = ['departure_airport', 'arrival_airport', 'departure_date'];
    for (let field of requiredFields) {
        if (!searchData[field]) {
            showAlert('Please fill in all required fields', 'warning');
            return;
        }
    }
    
    // Validate return date for round trips
    if (searchData.trip_type === 'round-trip' && !searchData.return_date) {
        showAlert('Please select a return date for round trips', 'warning');
        return;
    }
    
    // Submit form
    form.submit();
}

// Booking confirmation
function confirmBooking(flightId) {
    if (confirm('Are you sure you want to book this flight?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/passenger/book/${flightId}`;
        
        // Add search data as hidden fields
        const searchData = JSON.parse(localStorage.getItem('searchData') || '{}');
        for (let [key, value] of Object.entries(searchData)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            form.appendChild(input);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Refund confirmation
function confirmRefund(reservationId) {
    if (confirm('Are you sure you want to refund this booking? A 25% fee will be deducted.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/passenger/refund/${reservationId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Export functions for global access
window.SkyLink = {
    showAlert,
    makeRequest,
    searchFlights,
    confirmBooking,
    confirmRefund
}; 