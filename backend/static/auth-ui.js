/* Centralized login/logout UI — injects into nav bar on all pages */
(function () {
    var currentUser = null;

    // ── Modal HTML ──
    function showLoginModal() {
        if (document.getElementById('authModal')) return;

        var overlay = document.createElement('div');
        overlay.id = 'authModal';
        overlay.className = 'auth-modal-overlay';
        overlay.innerHTML =
            '<div class="auth-modal">' +
                '<button class="auth-modal-close" id="authModalClose">&times;</button>' +
                '<div class="auth-modal-header">' +
                    '<span class="auth-modal-icon">&#9876;</span>' +
                    '<h3 class="auth-modal-title">Join the Community</h3>' +
                '</div>' +
                '<p class="auth-modal-subtitle">Sign in with Google to unlock these features:</p>' +
                '<ul class="auth-modal-features">' +
                    '<li><span class="auth-feature-icon">&#128172;</span> <strong>Shoutbox</strong> — Chat with the community in real-time</li>' +
                    '<li><span class="auth-feature-icon">&#128221;</span> <strong>Forum</strong> — Create threads, post replies, and discuss</li>' +
                    '<li><span class="auth-feature-icon">&#128081;</span> <strong>Rank Badges</strong> — Earn RO job class ranks as you post</li>' +
                    '<li><span class="auth-feature-icon">&#128276;</span> <strong>Notifications</strong> — Get notified when someone replies to you</li>' +
                    '<li><span class="auth-feature-icon">&#128100;</span> <strong>Profile</strong> — Your own profile page with stats</li>' +
                '</ul>' +
                '<a href="/auth/login?redirect_to=' + encodeURIComponent(location.pathname) + '" class="auth-modal-btn">' +
                    '<svg class="auth-google-icon" viewBox="0 0 24 24" width="18" height="18"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>' +
                    'Continue with Google' +
                '</a>' +
                '<p class="auth-modal-note">We only access your name, email, and profile picture. No passwords stored.</p>' +
            '</div>';

        document.body.appendChild(overlay);

        // Close handlers
        document.getElementById('authModalClose').addEventListener('click', function () {
            overlay.remove();
        });
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) overlay.remove();
        });
    }

    // ── Inject auth controls into nav ──
    function renderAuthUI() {
        var nav = document.querySelector('.site-nav');
        if (!nav) return;

        // Remove existing auth element if any
        var existing = document.getElementById('navAuthUI');
        if (existing) existing.remove();

        var el = document.createElement('div');
        el.id = 'navAuthUI';
        el.className = 'nav-auth';

        if (currentUser) {
            var avatarHtml = currentUser.avatar_url
                ? '<img src="' + escapeHtml(currentUser.avatar_url) + '" class="nav-auth-avatar" alt="">'
                : '<span class="nav-auth-avatar-ph">' + escapeHtml(currentUser.display_name.charAt(0).toUpperCase()) + '</span>';

            el.innerHTML =
                '<a href="/forum/profile/' + currentUser.id + '" class="nav-auth-user" title="My Profile">' +
                    avatarHtml +
                    '<span class="nav-auth-name">' + escapeHtml(currentUser.display_name) + '</span>' +
                '</a>' +
                '<div class="nav-notif-wrapper" id="navNotifWrapper">' +
                    '<button class="nav-notif-bell" id="navNotifBell" title="Notifications">' +
                        '&#128276;<span class="nav-notif-badge" id="navNotifBadge" style="display:none;">0</span>' +
                    '</button>' +
                    '<div class="nav-notif-dropdown" id="navNotifDropdown"></div>' +
                '</div>' +
                '<a href="/auth/logout?redirect_to=' + encodeURIComponent(location.pathname) + '" class="nav-auth-logout" title="Sign Out">Sign Out</a>';
        } else {
            el.innerHTML = '<button class="nav-auth-login" id="navLoginBtn">Sign In</button>';
        }

        // Insert before the dark mode toggle
        var darkToggle = nav.querySelector('.dark-mode-toggle');
        if (darkToggle) {
            nav.insertBefore(el, darkToggle);
        } else {
            nav.appendChild(el);
        }

        // Bind modal
        if (!currentUser) {
            var btn = document.getElementById('navLoginBtn');
            if (btn) {
                btn.addEventListener('click', function () {
                    showLoginModal();
                });
            }
        }

        // Bind notification bell
        if (currentUser) {
            initNotifications();
        }
    }

    // ── Notifications ──
    function initNotifications() {
        var bell = document.getElementById('navNotifBell');
        var dropdown = document.getElementById('navNotifDropdown');
        var wrapper = document.getElementById('navNotifWrapper');
        if (!bell || !dropdown) return;

        // Fetch unread count
        fetch('/api/forum/notifications/count')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var badge = document.getElementById('navNotifBadge');
                if (badge && data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'flex';
                }
            })
            .catch(function () {});

        // Toggle dropdown
        bell.addEventListener('click', function (e) {
            e.stopPropagation();
            if (dropdown.classList.contains('open')) {
                dropdown.classList.remove('open');
                return;
            }
            dropdown.innerHTML = '<div class="nav-notif-loading">Loading...</div>';
            dropdown.classList.add('open');

            fetch('/api/forum/notifications')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (!data.items || !data.items.length) {
                        dropdown.innerHTML = '<div class="nav-notif-empty">No notifications yet.</div>';
                        return;
                    }
                    var html = '<div class="nav-notif-header">' +
                        '<span>Notifications</span>' +
                        '<button class="nav-notif-mark-read" id="navNotifMarkRead">Mark all read</button>' +
                    '</div>';
                    data.items.forEach(function (n) {
                        var avatarImg = n.actor_avatar
                            ? '<img class="nav-notif-avatar" src="' + escapeHtml(n.actor_avatar) + '" alt="">'
                            : '<span class="nav-notif-avatar-ph">' + escapeHtml((n.actor_name || '?').charAt(0).toUpperCase()) + '</span>';
                        html += '<a class="nav-notif-item' + (n.is_read ? '' : ' unread') + '" href="/forum/thread/' + n.thread_id + '">' +
                            avatarImg +
                            '<div>' +
                                '<div class="nav-notif-text"><strong>' + escapeHtml(n.actor_name) + '</strong> replied to <strong>' + escapeHtml(n.thread_title || 'a thread') + '</strong></div>' +
                                '<div class="nav-notif-time">' + timeAgo(n.created_at) + '</div>' +
                            '</div>' +
                        '</a>';
                    });
                    dropdown.innerHTML = html;

                    var markBtn = document.getElementById('navNotifMarkRead');
                    if (markBtn) {
                        markBtn.addEventListener('click', function (ev) {
                            ev.preventDefault();
                            ev.stopPropagation();
                            fetch('/api/forum/notifications/read', { method: 'POST' })
                                .then(function () {
                                    var badge = document.getElementById('navNotifBadge');
                                    if (badge) badge.style.display = 'none';
                                    var unread = dropdown.querySelectorAll('.nav-notif-item.unread');
                                    for (var i = 0; i < unread.length; i++) {
                                        unread[i].classList.remove('unread');
                                    }
                                })
                                .catch(function () {});
                        });
                    }
                })
                .catch(function () {
                    dropdown.innerHTML = '<div class="nav-notif-empty">Could not load notifications.</div>';
                });
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (wrapper && !wrapper.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });

        // Poll for new notifications every 60s
        setInterval(function () {
            fetch('/api/forum/notifications/count')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    var badge = document.getElementById('navNotifBadge');
                    if (badge) {
                        if (data.count > 0) {
                            badge.textContent = data.count > 99 ? '99+' : data.count;
                            badge.style.display = 'flex';
                        } else {
                            badge.style.display = 'none';
                        }
                    }
                })
                .catch(function () {});
        }, 60000);
    }

    // ── Init ──
    document.addEventListener('DOMContentLoaded', function () {
        fetch('/api/auth/me')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                currentUser = data && data.id ? data : null;
                renderAuthUI();
            })
            .catch(function () {
                renderAuthUI();
            });
    });
})();
