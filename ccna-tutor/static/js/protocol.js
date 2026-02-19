/**
 * Protocol Page Chat Functionality
 * Handles AI tutor chat interaction on protocol study pages
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');
    const chatContainer = document.getElementById('chat-container');
    const chatSubmitText = document.getElementById('chat-submit-text');
    const chatLoading = document.getElementById('chat-loading');

    if (!chatInput || !chatSubmit || !chatContainer) {
        return;
    }

    // Handle submit button click
    chatSubmit.addEventListener('click', function() {
        sendMessage();
    });

    // Handle Enter key in input
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const question = chatInput.value.trim();

        if (!question) {
            return;
        }

        // Disable input and show loading
        chatInput.disabled = true;
        chatSubmit.disabled = true;
        chatSubmitText.classList.add('d-none');
        chatLoading.classList.remove('d-none');

        // Add user message to chat
        addMessage('user', question);

        // Clear input
        chatInput.value = '';

        // Send to API
        fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                protocol_slug: window.protocolSlug,
                question: question
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessage('error', 'Error: ' + data.error);
            } else {
                addMessage('tutor', data.answer);
            }
        })
        .catch(error => {
            addMessage('error', 'Error: ' + error.message);
        })
        .finally(() => {
            // Re-enable input
            chatInput.disabled = false;
            chatSubmit.disabled = false;
            chatSubmitText.classList.remove('d-none');
            chatLoading.classList.add('d-none');
            chatInput.focus();
        });
    }

    function addMessage(type, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'mb-3 p-3 rounded ' + getMessageClass(type);

        if (type === 'user') {
            messageDiv.innerHTML = '<strong>You:</strong> ' + escapeHtml(text);
        } else if (type === 'tutor') {
            messageDiv.innerHTML = '<strong>AI Tutor:</strong> ' + formatTutorResponse(text);
        } else if (type === 'error') {
            messageDiv.innerHTML = '<strong>Error:</strong> ' + escapeHtml(text);
        }

        chatContainer.appendChild(messageDiv);
        messageDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function getMessageClass(type) {
        switch(type) {
            case 'user':
                return 'bg-light border border-secondary';
            case 'tutor':
                return 'bg-primary bg-opacity-10 border border-primary';
            case 'error':
                return 'bg-danger bg-opacity-10 border border-danger';
            default:
                return 'bg-light';
        }
    }

    function formatTutorResponse(text) {
        // Convert markdown-style formatting to HTML
        text = escapeHtml(text);
        
        // Bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
