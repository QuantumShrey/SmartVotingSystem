document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:5000/api';
    
    // Navigation elements
    const homeSection = document.getElementById('home-section');
    const voteSection = document.getElementById('vote-section');
    const registerSection = document.getElementById('register-section');
    const helpSection = document.getElementById('help-section');
    const contactSection = document.getElementById('contact-section');
    const homeSectionBtn = document.getElementById('home-section-btn');
    const voteSectionBtn = document.getElementById('vote-section-btn');
    const registerSectionBtn = document.getElementById('register-section-btn');
    const helpSectionBtn = document.getElementById('help-section-btn');
    const contactSectionBtn = document.getElementById('contact-section-btn');

    // Home page buttons
    const goToRegisterBtn = document.getElementById('go-to-register');
    const goToVoteBtn = document.getElementById('go-to-vote');

    // Status messages
    const voteStatusMessage = document.getElementById('status-message');
    const regStatusMessage = document.getElementById('reg-status-message');
    const registrationStatus = document.getElementById('registration-status');
    const messageOverlay = document.getElementById('message-overlay');
    const messageText = document.getElementById('message-text');

    // Function to show sections
    function showSection(sectionId) {
        [homeSection, voteSection, registerSection, helpSection, contactSection].forEach(section => {
            section.classList.add('hidden');
        });
        document.getElementById(sectionId).classList.remove('hidden');

        // Update active nav link
        [homeSectionBtn, voteSectionBtn, registerSectionBtn, helpSectionBtn, contactSectionBtn].forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[id="${sectionId}-btn"]`).classList.add('active');
    }

    // Navigation event listeners
    homeSectionBtn.addEventListener('click', () => showSection('home-section'));
    voteSectionBtn.addEventListener('click', () => showSection('vote-section'));
    registerSectionBtn.addEventListener('click', () => showSection('register-section'));
    helpSectionBtn.addEventListener('click', () => showSection('help-section'));
    contactSectionBtn.addEventListener('click', () => showSection('contact-section'));

    // Home page button listeners
    goToRegisterBtn.addEventListener('click', () => showSection('register-section'));
    goToVoteBtn.addEventListener('click', () => showSection('vote-section'));

    // Function to show message overlay
    function showMessage(message, duration = 3000) {
        messageText.textContent = message;
        messageOverlay.style.display = 'flex';
        if (duration > 0) {
            setTimeout(() => {
                messageOverlay.style.display = 'none';
            }, duration);
        }
    }

    // Handle keyboard events for voting
    document.addEventListener('keydown', async (event) => {
        // Only process key events when vote section is visible
        if (!voteSection.classList.contains('hidden')) {
            const key = event.key;
            let party;
            switch(key) {
                case '1':
                    party = 'BJP';
                    break;
                case '2':
                    party = 'Congress';
                    break;
                case '3':
                    party = 'AAP';
                    break;
                case '4':
                    party = 'NOTA';
                    break;
                default:
                    return;
            }

            try {
                showMessage(`Processing your vote for ${party}...`, 0);
                const response = await fetch(`${API_URL}/verify-and-vote`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ vote: party })
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    showMessage(data.message, 5000);
                    // Clean up video capture
                    await fetch(`${API_URL}/cleanup`, {
                        method: 'POST'
                    });
                } else {
                    showMessage(data.message, 3000);
                }
            } catch (error) {
                showMessage('Error processing vote. Please try again.', 3000);
                console.error('Error:', error);
            }
        }
    });

    // Update vote status message
    function updateVoteStatus(message) {
        voteStatusMessage.textContent = message;
    }

    // Update registration status message
    function updateRegStatus(message) {
        regStatusMessage.textContent = message;
    }

    // Handle registration form
    const aadharInput = document.getElementById('aadhar');
    const startRegistrationBtn = document.getElementById('start-registration');

    aadharInput.addEventListener('input', (e) => {
        // Only allow numbers
        e.target.value = e.target.value.replace(/\D/g, '');
        
        // Limit to 12 digits
        if (e.target.value.length > 12) {
            e.target.value = e.target.value.slice(0, 12);
        }
    });

    startRegistrationBtn.addEventListener('click', async () => {
        const aadhar = aadharInput.value;
        if (aadhar.length !== 12) {
            showMessage('Please enter a valid 12-digit Aadhar number');
            return;
        }

        try {
            updateRegStatus('Starting face registration...');
            registrationStatus.textContent = 'Please look at the camera and wait for the registration process to complete.';
            startRegistrationBtn.disabled = true;
            showMessage('Registration in progress... Please wait', 0);

            const response = await fetch(`${API_URL}/start-registration`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ aadhar })
            });
            const data = await response.json();

            if (data.status === 'success') {
                showMessage(data.message, 5000);
                registrationStatus.textContent = 'Registration completed successfully!';
                // Clean up video capture
                await fetch(`${API_URL}/cleanup`, {
                    method: 'POST'
                });
            } else {
                showMessage(data.message, 3000);
                registrationStatus.textContent = 'Registration failed. Please try again.';
            }
        } catch (error) {
            showMessage('Error during registration. Please try again.', 3000);
            console.error('Error:', error);
        } finally {
            startRegistrationBtn.disabled = false;
        }
    });

    // Initial status
    updateVoteStatus('Please look at the camera for verification');
});
