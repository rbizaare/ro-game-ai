/* Shoutbox — lightweight real-time chat for the homepage */
(function () {
    var container = document.getElementById('shoutboxMessages');
    var form = document.getElementById('shoutboxForm');
    var input = document.getElementById('shoutboxInput');
    var charCount = document.getElementById('shoutboxCharCount');
    var loginPrompt = document.getElementById('shoutboxLoginPrompt');
    if (!container) return;

    var MAX_MESSAGES = 50;
    var MAX_CHARS = 200;
    var currentUser = null;
    var ws = null;

    function escapeHtml(s) {
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function timeAgo(iso) {
        var diff = (Date.now() - new Date(iso).getTime()) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        return Math.floor(diff / 86400) + 'd ago';
    }

    function renderMessage(msg) {
        var avatarHtml = msg.avatar_url
            ? '<img src="' + escapeHtml(msg.avatar_url) + '" class="shoutbox-avatar-img" alt="">'
            : '<span class="shoutbox-avatar-placeholder">' + escapeHtml(msg.display_name.charAt(0).toUpperCase()) + '</span>';

        return '<div class="shoutbox-msg">' +
            '<div class="shoutbox-avatar">' + avatarHtml + '</div>' +
            '<div class="shoutbox-msg-body">' +
                '<span class="shoutbox-msg-header">' +
                    '<a href="/forum/profile/' + msg.user_id + '" class="shoutbox-name">' + escapeHtml(msg.display_name) + '</a>' +
                    (msg.rank_title ? ' <span class="rank-badge">' + escapeHtml(msg.rank_title) + '</span>' : '') +
                    ' <span class="shoutbox-time">' + timeAgo(msg.created_at) + '</span>' +
                '</span>' +
                '<span class="shoutbox-text">' + escapeHtml(msg.message) + '</span>' +
            '</div>' +
        '</div>';
    }

    function scrollToBottom() {
        container.scrollTop = container.scrollHeight;
    }

    function trimMessages() {
        while (container.children.length > MAX_MESSAGES) {
            container.removeChild(container.firstChild);
        }
    }

    function appendMessage(msg) {
        var div = document.createElement('div');
        div.innerHTML = renderMessage(msg);
        container.appendChild(div.firstChild);
        trimMessages();
        scrollToBottom();
    }

    // Load initial messages
    fetch('/api/shoutbox/messages')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            container.innerHTML = '';
            (data.messages || []).forEach(function (msg) {
                var div = document.createElement('div');
                div.innerHTML = renderMessage(msg);
                container.appendChild(div.firstChild);
            });
            scrollToBottom();
        });

    // Check auth
    fetch('/api/auth/me')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            currentUser = data.user || null;
            if (currentUser && form) {
                form.style.display = 'flex';
                if (loginPrompt) loginPrompt.style.display = 'none';
            }
        });

    // WebSocket for real-time updates
    function connectWs() {
        var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(protocol + '//' + location.host + '/ws/shoutbox');

        ws.onmessage = function (e) {
            try {
                var msg = JSON.parse(e.data);
                appendMessage(msg);
            } catch (err) { /* ignore */ }
        };

        ws.onclose = function () {
            setTimeout(connectWs, 3000);
        };
    }
    connectWs();

    // Character counter
    if (input && charCount) {
        input.addEventListener('input', function () {
            var len = input.value.length;
            charCount.textContent = len + '/' + MAX_CHARS;
            charCount.classList.toggle('over-limit', len > MAX_CHARS - 20);
        });
    }

    // Form submit
    if (form && input) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var text = input.value.trim();
            if (!text || text.length > MAX_CHARS) return;

            fetch('/api/shoutbox/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            })
                .then(function (r) {
                    if (r.status === 429) {
                        alert('Slow down! Max 10 messages per minute.');
                        return;
                    }
                    if (r.status === 401) {
                        window.location.href = '/auth/login';
                        return;
                    }
                    if (r.ok) {
                        input.value = '';
                        if (charCount) charCount.textContent = '0/' + MAX_CHARS;
                    }
                });
        });
    }
})();
