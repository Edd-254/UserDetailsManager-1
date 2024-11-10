document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('registrationForm');
    const editForm = document.getElementById('editProfileForm');
    
    // Function to setup phone input formatting
    const setupPhoneInput = (phoneInput) => {
        if (phoneInput) {
            phoneInput.addEventListener('input', function(e) {
                let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
                e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
            });
        }
    };

    // Function to validate form
    const setupFormValidation = (form) => {
        if (!form) return;

        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            // Password validation (only for registration form)
            const password = document.getElementById('password');
            if (password) {
                const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]/;
                if (!passwordRegex.test(password.value)) {
                    event.preventDefault();
                    password.classList.add('is-invalid');
                }
            }

            // User ID validation (only for registration form)
            const userId = document.getElementById('user_id');
            if (userId) {
                const userIdRegex = /^[A-Za-z0-9]{4,20}$/;
                if (!userIdRegex.test(userId.value)) {
                    event.preventDefault();
                    userId.classList.add('is-invalid');
                }
            }

            // Email validation
            const email = document.getElementById(form.id === 'registrationForm' ? 'email' : 'email');
            if (email) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email.value)) {
                    event.preventDefault();
                    email.classList.add('is-invalid');
                }
            }

            form.classList.add('was-validated');
        });
    };

    // Setup phone formatting for both forms
    setupPhoneInput(document.getElementById('phone'));
    
    // Setup form validation for both forms
    setupFormValidation(form);
    setupFormValidation(editForm);
});
