/* Shoutbox — floating chat bubble (like FB Messenger), visible on all pages */
(function () {
    var MAX_MESSAGES = 50;
    var MAX_CHARS = 200;
    var currentUser = null;
    var ws = null;
    var isOpen = false;
    var unreadCount = 0;

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

    // ── Inject HTML ──
    var wrapper = document.createElement('div');
    wrapper.id = 'shoutbox-float';
    wrapper.innerHTML =
        '<button class="shoutbox-bubble" id="shoutboxBubble" title="Community Shoutbox">' +
            '<span class="shoutbox-bubble-icon">&#128172;</span>' +
            '<span class="shoutbox-bubble-badge" id="shoutboxBadge" style="display:none;">0</span>' +
        '</button>' +
        '<div class="shoutbox-panel" id="shoutboxPanel" style="display:none;">' +
            '<div class="shoutbox-panel-header">' +
                '<span class="shoutbox-panel-title">Shoutbox</span>' +
                '<button class="shoutbox-panel-close" id="shoutboxClose">&times;</button>' +
            '</div>' +
            '<div class="shoutbox-panel-messages" id="shoutboxMessages"></div>' +
            '<div class="shoutbox-panel-footer" id="shoutboxFooter">' +
                '<p class="shoutbox-panel-login" id="shoutboxLoginPrompt">' +
                    '<a href="/auth/login?redirect_to=' + encodeURIComponent(location.pathname) + '">Sign in</a> to chat' +
                '</p>' +
                '<form class="shoutbox-panel-form" id="shoutboxForm" style="display:none;">' +
                    '<button type="button" class="shoutbox-emote-btn" id="shoutboxEmoteBtn" title="Emotes">&#128522;</button>' +
                    '<input type="text" id="shoutboxInput" class="shoutbox-panel-input" placeholder="Say something... (use /heh /lv etc.)" maxlength="200" autocomplete="off">' +
                    '<button type="submit" class="shoutbox-panel-send">&#10148;</button>' +
                '</form>' +
                '<div class="shoutbox-emote-picker" id="shoutboxEmotePicker" style="display:none;"></div>' +
            '</div>' +
        '</div>';
    document.body.appendChild(wrapper);

    var bubble = document.getElementById('shoutboxBubble');
    var badge = document.getElementById('shoutboxBadge');
    var panel = document.getElementById('shoutboxPanel');
    var closeBtn = document.getElementById('shoutboxClose');
    var container = document.getElementById('shoutboxMessages');
    var form = document.getElementById('shoutboxForm');
    var input = document.getElementById('shoutboxInput');
    var loginPrompt = document.getElementById('shoutboxLoginPrompt');

    // ── Toggle panel ──
    bubble.addEventListener('click', function () {
        isOpen = !isOpen;
        panel.style.display = isOpen ? 'flex' : 'none';
        bubble.classList.toggle('active', isOpen);
        if (isOpen) {
            unreadCount = 0;
            badge.style.display = 'none';
            scrollToBottom();
            if (input && currentUser) input.focus();
        }
    });

    closeBtn.addEventListener('click', function () {
        isOpen = false;
        panel.style.display = 'none';
        bubble.classList.remove('active');
    });

    // ── Rendering ──
    function renderMessage(msg) {
        var avatarHtml = msg.avatar_url
            ? '<img src="' + escapeHtml(msg.avatar_url) + '" class="sb-msg-avatar-img" alt="">'
            : '<span class="sb-msg-avatar-ph">' + escapeHtml(msg.display_name.charAt(0).toUpperCase()) + '</span>';

        return '<div class="sb-msg">' +
            '<div class="sb-msg-avatar">' + avatarHtml + '</div>' +
            '<div class="sb-msg-body">' +
                '<div class="sb-msg-header">' +
                    '<span class="sb-msg-name">' + escapeHtml(msg.display_name) + '</span>' +
                    '<span class="sb-msg-time">' + timeAgo(msg.created_at) + '</span>' +
                '</div>' +
                '<div class="sb-msg-text">' + renderEmotesInHtml(escapeHtml(msg.message)) + '</div>' +
            '</div>' +
        '</div>';
    }

    function scrollToBottom() {
        container.scrollTop = container.scrollHeight;
    }

    function appendMessage(msg) {
        var div = document.createElement('div');
        div.innerHTML = renderMessage(msg);
        container.appendChild(div.firstChild);
        while (container.children.length > MAX_MESSAGES) {
            container.removeChild(container.firstChild);
        }
        if (isOpen) {
            scrollToBottom();
        } else {
            unreadCount++;
            badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
            badge.style.display = 'flex';
        }
    }

    // ── Load messages ──
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

    // ── Auth check ──
    fetch('/api/auth/me')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            currentUser = data && data.id ? data : null;
            if (currentUser && form) {
                form.style.display = 'flex';
                if (loginPrompt) loginPrompt.style.display = 'none';
            }
        });

    // ── WebSocket ──
    function connectWs() {
        var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(protocol + '//' + location.host + '/ws/shoutbox');
        ws.onmessage = function (e) {
            try { appendMessage(JSON.parse(e.data)); } catch (err) { /* ignore */ }
        };
        ws.onclose = function () { setTimeout(connectWs, 3000); };
    }
    connectWs();

    // ── Emote Picker ──
    var emoteBtn = document.getElementById('shoutboxEmoteBtn');
    var emotePicker = document.getElementById('shoutboxEmotePicker');
    var emotePickerOpen = false;

    if (emotePicker && typeof RO_EMOTES !== 'undefined') {
        var grid = '';
        RO_EMOTES.forEach(function (e) {
            grid += '<button type="button" class="emote-pick" data-cmd="' + e.cmd + '" title="' + e.cmd + ' ' + e.name + '">' +
                '<img src="/static/emotes/' + e.file + '" alt="' + e.cmd + '">' +
            '</button>';
        });
        emotePicker.innerHTML = grid;

        emotePicker.addEventListener('click', function (ev) {
            var btn = ev.target.closest('.emote-pick');
            if (!btn) return;
            var cmd = btn.getAttribute('data-cmd');
            if (input) {
                var v = input.value;
                input.value = v + (v && !v.endsWith(' ') ? ' ' : '') + cmd + ' ';
                input.focus();
            }
        });
    }

    if (emoteBtn) {
        emoteBtn.addEventListener('click', function () {
            emotePickerOpen = !emotePickerOpen;
            emotePicker.style.display = emotePickerOpen ? 'grid' : 'none';
            emoteBtn.classList.toggle('active', emotePickerOpen);
        });
    }

    // ── Send message ──
    if (form && input) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var text = input.value.trim();
            if (!text || text.length > MAX_CHARS) return;

            // Close emote picker on send
            if (emotePickerOpen) {
                emotePickerOpen = false;
                emotePicker.style.display = 'none';
                if (emoteBtn) emoteBtn.classList.remove('active');
            }

            fetch('/api/shoutbox/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            }).then(function (r) {
                if (r.status === 429) { alert('Slow down! Max 10 messages per minute.'); return; }
                if (r.status === 401) { window.location.href = '/auth/login?redirect_to=' + encodeURIComponent(location.pathname); return; }
                if (r.ok) { input.value = ''; }
            });
        });
    }
})();
