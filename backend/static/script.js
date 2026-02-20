const form = document.getElementById('chatForm');
const input = document.getElementById('chatInput');
const messages = document.getElementById('chatMessages');
const sendBtn = document.getElementById('sendBtn');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question = input.value.trim();
    if (!question) return;

    appendMessage(question, 'user');
    input.value = '';

    const typingEl = showTypingIndicator();

    sendBtn.disabled = true;
    input.disabled = true;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();
        removeTypingIndicator(typingEl);
        appendMessage(data.answer, 'bot');
    } catch (err) {
        removeTypingIndicator(typingEl);
        appendMessage('Sorry, something went wrong. Please try again.', 'bot');
    } finally {
        sendBtn.disabled = false;
        input.disabled = false;
        input.focus();
    }
});

function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    div.appendChild(content);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function showTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message bot-message typing';
    div.innerHTML = '<div class="message-content"><span></span><span></span><span></span></div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

function removeTypingIndicator(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

// Allow Enter to send, Shift+Enter for newline (future multiline support)
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        form.dispatchEvent(new Event('submit'));
    }
});

// Commands modal
const commandsBtn = document.getElementById('commandsBtn');
const commandsModal = document.getElementById('commandsModal');
const modalClose = document.getElementById('modalClose');

commandsBtn.addEventListener('click', () => {
    commandsModal.classList.add('active');
});

modalClose.addEventListener('click', () => {
    commandsModal.classList.remove('active');
});

// Close modal on overlay click
commandsModal.addEventListener('click', (e) => {
    if (e.target === commandsModal) {
        commandsModal.classList.remove('active');
    }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        commandsModal.classList.remove('active');
    }
});

// Click a command example to auto-fill input
document.querySelectorAll('.cmd-item').forEach(item => {
    item.addEventListener('click', () => {
        const query = item.getAttribute('data-query');
        if (query) {
            input.value = query;
            commandsModal.classList.remove('active');
            input.focus();
        }
    });
});
