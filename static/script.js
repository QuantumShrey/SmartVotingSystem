document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:5000/api';
    
    // Navigation elements
    const sections = {
        'home': document.getElementById('home-section'),
        'vote': document.getElementById('vote-section'),
        'register': document.getElementById('register-section'),
        'help': document.getElementById('help-section'),
        'contact': document.getElementById('contact-section')
    };

    // Navigation buttons
    const navButtons = {
        'home': document.getElementById('home-section-btn'),
        'vote': document.getElementById('vote-section-btn'),
        'register': document.getElementById('register-section-btn'),
        'help': document.getElementById('help-section-btn'),
        'contact': document.getElementById('contact-section-btn')
    };

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
    function showSection(sectionName) {
        // Hide all sections
        Object.values(sections).forEach(section => {
            if (section) section.classList.add('hidden');
        });

        // Show the selected section
        const selectedSection = sections[sectionName];
        if (selectedSection) {
            selectedSection.classList.remove('hidden');
        }

        // Update active nav button
        Object.values(navButtons).forEach(btn => {
            if (btn) btn.classList.remove('active');
        });
        const activeButton = navButtons[sectionName];
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }

    // Add click event listeners to navigation buttons
    Object.entries(navButtons).forEach(([sectionName, button]) => {
        if (button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                showSection(sectionName);
            });
        }
    });

    // Home page button listeners
    if (goToRegisterBtn) {
        goToRegisterBtn.addEventListener('click', () => showSection('register'));
    }
    if (goToVoteBtn) {
        goToVoteBtn.addEventListener('click', () => showSection('vote'));
    }

    // Function to show message overlay
    function showMessage(message, duration = 3000) {
        if (messageText && messageOverlay) {
            messageText.textContent = message;
            messageOverlay.style.display = 'flex';
            if (duration > 0) {
                setTimeout(() => {
                    messageOverlay.style.display = 'none';
                }, duration);
            }
        }
    }

    // Video feed functions
    function startVideo() {
        const videoFeed = document.getElementById('video-feed');
        if (videoFeed) {
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                videoFeed.src = '/video_feed';
            } else {
                // In production, show a message about webcam limitations
                const webcamContainer = document.querySelector('.webcam-container');
                if (webcamContainer) {
                    webcamContainer.innerHTML = `
                        <div class="alert alert-info">
                            <h4>Webcam Access Limited</h4>
                            <p>For security reasons, webcam access is only available when running the application locally.</p>
                            <p>Please download and run the application locally to use facial recognition features.</p>
                        </div>
                    `;
                }
            }
        }
    }

    // Handle keyboard events for voting
    document.addEventListener('keydown', async (event) => {
        // Only process key events when vote section is visible
        if (!sections['vote'].classList.contains('hidden')) {
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
            registrationStatus.textContent = 'Starting registration... Please look at the camera.';
            startRegistrationBtn.disabled = true;

            const response = await fetch(`${API_URL}/start-registration`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ aadhar })
            });

            const data = await response.json();

            if (data.success) {
                showMessage('Registration successful!', 5000);
                registrationStatus.textContent = 'Registration completed successfully!';
                // Reset form
                aadharInput.value = '';
            } else {
                showMessage(data.error || 'Registration failed. Please try again.', 3000);
                registrationStatus.textContent = data.error || 'Registration failed. Please try again.';
            }
        } catch (error) {
            console.error('Registration error:', error);
            showMessage('Error during registration. Please try again.', 3000);
            registrationStatus.textContent = 'Registration failed. Please try again.';
        } finally {
            startRegistrationBtn.disabled = false;
        }
    });

    // Initial status
    updateVoteStatus('Please look at the camera for verification');
});
