// JS file placeholder – add interactivity if needed
document.addEventListener("DOMContentLoaded", function () {
    const tripTypeInputs = document.querySelectorAll('input[name="trip_type"]');
    const returnDateInput = document.querySelector('input[name="return_date"]');

    tripTypeInputs.forEach(input => {
        input.addEventListener('change', function () {
            if (this.value === 'one-way') {
                returnDateInput.disabled = true;
                returnDateInput.value = '';
            } else {
                returnDateInput.disabled = false;
            }
        });
    });

    // Trigger the correct state on page load
    if (document.querySelector('input[name="trip_type"]:checked').value === 'one-way') {
        returnDateInput.disabled = true;
    }
});
