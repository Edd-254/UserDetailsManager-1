document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registrationForm');
    
    // Phone number formatting
    const phoneInput = document.getElementById('phone');
    phoneInput.addEventListener('input', function(e) {
        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
        e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
    });

    // Client-side validation
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }

        const password = document.getElementById('password').value;
        const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]/;
        if (!passwordRegex.test(password)) {
            event.preventDefault();
            document.getElementById('password').classList.add('is-invalid');
        }

        const userId = document.getElementById('user_id').value;
        const userIdRegex = /^[A-Za-z0-9]{4,20}$/;
        if (!userIdRegex.test(userId)) {
            event.preventDefault();
            document.getElementById('user_id').classList.add('is-invalid');
        }

        const email = document.getElementById('email').value;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            event.preventDefault();
            document.getElementById('email').classList.add('is-invalid');
        }

        form.classList.add('was-validated');
    });
});
