document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements only if they exist
    const initializeForms = () => {
        const forms = {
            registration: document.getElementById('registrationForm'),
            edit: document.getElementById('editProfileForm')
        };

        // Function to setup phone input formatting
        const setupPhoneInput = (form) => {
            const phoneInput = form ? form.querySelector('#phone') : null;
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
                let isValid = true;

                // Clear previous validation states
                form.querySelectorAll('.is-invalid').forEach(element => {
                    element.classList.remove('is-invalid');
                });

                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    isValid = false;
                }

                // Password validation (only for registration form)
                if (form.id === 'registrationForm') {
                    const password = form.querySelector('#password');
                    if (password) {
                        const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]/;
                        if (!passwordRegex.test(password.value)) {
                            password.classList.add('is-invalid');
                            isValid = false;
                        }
                    }

                    const userId = form.querySelector('#user_id');
                    if (userId) {
                        const userIdRegex = /^[A-Za-z0-9]{4,20}$/;
                        if (!userIdRegex.test(userId.value)) {
                            userId.classList.add('is-invalid');
                            isValid = false;
                        }
                    }
                }

                // Common validations for both forms
                const email = form.querySelector('#email');
                if (email) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(email.value)) {
                        email.classList.add('is-invalid');
                        isValid = false;
                    }
                }

                const phone = form.querySelector('#phone');
                if (phone) {
                    const phoneRegex = /^\(\d{3}\) \d{3}-\d{4}$/;
                    if (!phoneRegex.test(phone.value)) {
                        phone.classList.add('is-invalid');
                        isValid = false;
                    }
                }

                // Required field validation
                ['first_name', 'last_name', 'address', 'gender'].forEach(fieldId => {
                    const field = form.querySelector(`#${fieldId}`);
                    if (field && !field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    }
                });

                if (!isValid) {
                    event.preventDefault();
                }
                form.classList.add('was-validated');
            });
        };

        // Initialize each form if it exists
        Object.values(forms).forEach(form => {
            if (form) {
                setupPhoneInput(form);
                setupFormValidation(form);
            }
        });
    };

    // Call initialization
    initializeForms();
});
