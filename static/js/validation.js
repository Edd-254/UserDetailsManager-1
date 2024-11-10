document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing form validation');
    
    const initializeForms = () => {
        try {
            // Use document body as parent for event delegation
            document.body.addEventListener('submit', function(event) {
                const form = event.target;
                if (!form.matches('#registrationForm, #editProfileForm')) return;
                
                console.log(`Form submission started for: ${form.id}`);
                let isValid = true;

                // Clear previous validation states
                form.querySelectorAll('.is-invalid').forEach(element => {
                    element.classList.remove('is-invalid');
                });

                // Basic form validity check
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    isValid = false;
                    console.log('Basic form validity check failed');
                }

                // Password validation (only for registration form)
                if (form.id === 'registrationForm') {
                    const password = form.querySelector('#password');
                    if (password) {
                        const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]/;
                        if (!passwordRegex.test(password.value)) {
                            password.classList.add('is-invalid');
                            isValid = false;
                            console.log('Password validation failed');
                        }
                    }

                    const userId = form.querySelector('#user_id');
                    if (userId) {
                        const userIdRegex = /^[A-Za-z0-9]{4,20}$/;
                        if (!userIdRegex.test(userId.value)) {
                            userId.classList.add('is-invalid');
                            isValid = false;
                            console.log('User ID validation failed');
                        }
                    }
                }

                // Common validations for both forms
                const validations = {
                    email: {
                        selector: '#email',
                        regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: 'Invalid email format'
                    },
                    phone: {
                        selector: '#phone',
                        regex: /^\(\d{3}\) \d{3}-\d{4}$/,
                        message: 'Invalid phone format'
                    }
                };

                Object.entries(validations).forEach(([field, validation]) => {
                    const element = form.querySelector(validation.selector);
                    if (element && !validation.regex.test(element.value)) {
                        element.classList.add('is-invalid');
                        isValid = false;
                        console.log(`${field} validation failed`);
                    }
                });

                // Required field validation
                ['first_name', 'last_name', 'address', 'gender'].forEach(fieldId => {
                    const field = form.querySelector(`#${fieldId}`);
                    if (field && !field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                        console.log(`Required field validation failed: ${fieldId}`);
                    }
                });

                if (!isValid) {
                    event.preventDefault();
                    console.log('Form submission prevented due to validation errors');
                } else {
                    console.log('Form validation successful');
                }
                
                form.classList.add('was-validated');
            });

            // Setup phone input formatting using event delegation
            document.body.addEventListener('input', function(event) {
                const input = event.target;
                if (input.matches('#phone')) {
                    let x = input.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
                    input.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
                    console.log(`Phone input formatting applied`);
                }
            });

            console.log('Form validation initialized with event delegation');
        } catch (error) {
            console.error('Error during form initialization:', error);
        }
    };

    // Initialize validation
    initializeForms();
});