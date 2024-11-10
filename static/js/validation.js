document.addEventListener('DOMContentLoaded', function() {
    // Logging initialization for debugging
    console.log('DOM Content Loaded - Initializing form validation');
    
    // Initialize form elements with error handling
    const initializeForms = () => {
        try {
            const forms = {
                registration: document.getElementById('registrationForm'),
                edit: document.getElementById('editProfileForm')
            };

            // Log which forms were found
            Object.entries(forms).forEach(([key, form]) => {
                console.log(`${key} form ${form ? 'found' : 'not found'}`);
            });

            // Function to setup phone input formatting
            const setupPhoneInput = (form) => {
                if (!form) return;
                
                const phoneInput = form.querySelector('#phone');
                if (phoneInput) {
                    phoneInput.addEventListener('input', function(e) {
                        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
                        e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
                    });
                    console.log(`Phone input formatting setup for form: ${form.id}`);
                }
            };

            // Function to validate form
            const setupFormValidation = (form) => {
                if (!form) return;
                console.log(`Setting up validation for form: ${form.id}`);

                form.addEventListener('submit', function(event) {
                    let isValid = true;
                    console.log(`Form submission started for: ${form.id}`);

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
            };

            // Initialize each form if it exists
            Object.values(forms).forEach(form => {
                if (form) {
                    try {
                        setupPhoneInput(form);
                        setupFormValidation(form);
                        console.log(`Successfully initialized form: ${form.id}`);
                    } catch (error) {
                        console.error(`Error initializing form ${form.id}:`, error);
                    }
                }
            });

        } catch (error) {
            console.error('Error during form initialization:', error);
        }
    };

    // Call initialization with error handling
    try {
        initializeForms();
    } catch (error) {
        console.error('Fatal error during form initialization:', error);
    }
});
