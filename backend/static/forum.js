/* ===== Forum JavaScript ===== */

let _currentUser = null;

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function timeAgo(iso) {
    if (!iso) return '';
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 2592000) return Math.floor(diff / 86400) + 'd ago';
    return new Date(iso).toLocaleDateString();
}

// ── Auth ──

async function fetchCurrentUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        _currentUser = data;
    } catch {
        _currentUser = null;
    }
    renderAuthBar();
}

function renderAuthBar() {
    const bar = document.getElementById('authBar');
    if (!bar) return;
    if (_currentUser) {
        bar.innerHTML = `
            <div class="forum-auth-user">
                <img class="forum-auth-avatar" src="${escapeHtml(_currentUser.avatar_url)}" alt="">
                <a href="/forum/profile/${_currentUser.id}" style="color:inherit;text-decoration:none;">${escapeHtml(_currentUser.display_name)}</a>
                ${_currentUser.is_admin ? '<span style="font-size:0.7rem;color:var(--ro-gold);font-weight:600;">ADMIN</span>' : ''}
            </div>
        `;
    } else {
        bar.innerHTML = '<a href="/auth/login" class="btn-google">Sign in with Google</a>';
    }
}

// ── Routing ──

function getRoute() {
    const hash = window.location.hash.slice(1);
    if (!hash) return { view: 'categories' };
    const parts = hash.split('/');
    if (parts[0] === 'category' && parts[1]) {
        return { view: 'threads', slug: parts[1], page: parseInt(parts[2]) || 1 };
    }
    if (parts[0] === 'search' && parts[1]) {
        return { view: 'search', query: decodeURIComponent(parts[1]), page: parseInt(parts[2]) || 1 };
    }
    return { view: 'categories' };
}

function navigate(hash) {
    window.location.hash = hash;
}

// ── Search ──

function renderSearchBar() {
    return `
        <div class="forum-search-bar">
            <input class="forum-search-input" id="searchInput" type="text" placeholder="Search threads..."
                   onkeydown="if(event.key==='Enter')doSearch()">
            <button class="forum-search-btn" onclick="doSearch()">Search</button>
        </div>
    `;
}

function doSearch() {
    const q = document.getElementById('searchInput').value.trim();
    if (q.length < 2) return alert('Search query must be at least 2 characters.');
    navigate('search/' + encodeURIComponent(q));
}

async function renderSearchResults(query, page) {
    const content = document.getElementById('forumContent');
    const breadcrumb = document.getElementById('breadcrumb');
    breadcrumb.style.display = 'flex';
    breadcrumb.innerHTML = `<a href="#">Forum</a> <span>/</span> <span>Search: "${escapeHtml(query)}"</span>`;

    try {
        const res = await fetch(`/api/forum/search?q=${encodeURIComponent(query)}&page=${page}`);
        if (!res.ok) throw new Error('Search failed');
        const data = await res.json();

        let resultsHtml;
        if (!data.items.length) {
            resultsHtml = '<div class="forum-empty">No threads found matching your search.</div>';
        } else {
            resultsHtml = `
                <div class="forum-threads-wrap">
                    ${data.items.map(t => `
                        <a class="forum-thread-row" href="/forum/thread/${t.id}">
                            <img class="forum-thread-avatar" src="${escapeHtml(t.author_avatar)}" alt="" onerror="this.style.display='none'">
                            <div class="forum-thread-info">
                                <div class="forum-thread-title"><span>${escapeHtml(t.title)}</span></div>
                                <div class="forum-thread-sub">by ${escapeHtml(t.author_name)} in ${escapeHtml(t.category_name)} &middot; ${timeAgo(t.created_at)}</div>
                            </div>
                            <div class="forum-thread-stats">
                                <div class="forum-thread-replies">${t.reply_count}</div>
                            </div>
                        </a>
                    `).join('')}
                </div>
            `;
        }

        const totalPages = Math.ceil(data.total / data.per_page);
        let paginationHtml = '';
        if (totalPages > 1) {
            paginationHtml = '<div class="forum-pagination">';
            for (let i = 1; i <= totalPages; i++) {
                paginationHtml += `<a class="forum-page-btn ${i === page ? 'active' : ''}" href="#search/${encodeURIComponent(query)}/${i}">${i}</a>`;
            }
            paginationHtml += '</div>';
        }

        content.innerHTML = `
            ${renderSearchBar()}
            <h2 style="font-family:'Cinzel',serif;font-size:1rem;margin-bottom:1rem;">${data.total} result${data.total !== 1 ? 's' : ''} for "${escapeHtml(query)}"</h2>
            ${resultsHtml}
            ${paginationHtml}
        `;
        document.getElementById('searchInput').value = query;
    } catch {
        content.innerHTML = renderSearchBar() + '<div class="forum-empty">Search failed.</div>';
    }
}

// ── Categories View ──

async function renderCategories() {
    const content = document.getElementById('forumContent');
    const breadcrumb = document.getElementById('breadcrumb');
    breadcrumb.style.display = 'none';

    try {
        const res = await fetch('/api/forum/categories');
        const categories = await res.json();

        if (!categories.length) {
            content.innerHTML = renderSearchBar() + '<div class="forum-empty">No categories found.</div>';
            return;
        }

        content.innerHTML = `
            ${renderSearchBar()}
            <div class="forum-categories">
                ${categories.map(cat => `
                    <a class="forum-category-card" href="#category/${escapeHtml(cat.slug)}">
                        <div class="forum-category-header">
                            <h3>${escapeHtml(cat.name)}</h3>
                        </div>
                        <div class="forum-category-body">
                            <p class="forum-category-desc">${escapeHtml(cat.description)}</p>
                            <div class="forum-category-meta">
                                <span><strong>${cat.thread_count}</strong> threads</span>
                                <span>${cat.latest_activity ? timeAgo(cat.latest_activity) : 'No activity'}</span>
                            </div>
                        </div>
                    </a>
                `).join('')}
            </div>
        `;
    } catch {
        content.innerHTML = '<div class="forum-empty">Failed to load categories.</div>';
    }
}

// ── Threads View ──

async function renderThreads(slug, page) {
    const content = document.getElementById('forumContent');
    const breadcrumb = document.getElementById('breadcrumb');

    try {
        const res = await fetch(`/api/forum/categories/${encodeURIComponent(slug)}/threads?page=${page}`);
        if (!res.ok) throw new Error('Not found');
        const data = await res.json();
        const cat = data.category;

        breadcrumb.style.display = 'flex';
        breadcrumb.innerHTML = `<a href="#"> Forum</a> <span>/</span> <span>${escapeHtml(cat.name)}</span>`;

        const newThreadBtn = _currentUser
            ? `<button class="btn-new-thread" onclick="toggleNewThread()">+ New Thread</button>`
            : '';

        const newThreadForm = _currentUser ? `
            <div class="forum-new-thread" id="newThreadForm">
                <h3>Create New Thread</h3>
                <input class="forum-input" id="threadTitle" type="text" placeholder="Thread title" maxlength="200">
                <textarea class="forum-input forum-textarea" id="threadBody" placeholder="Write your post..." maxlength="10000"></textarea>
                <div class="forum-form-actions">
                    <button class="btn-cancel" onclick="toggleNewThread()">Cancel</button>
                    <button class="btn-submit" id="submitThread" onclick="submitNewThread('${escapeHtml(slug)}')">Post Thread</button>
                </div>
            </div>
        ` : '';

        const loginPrompt = !_currentUser
            ? `<div class="forum-login-prompt"><a href="/auth/login">Sign in with Google</a> to create threads and replies.</div>`
            : '';

        let threadsHtml;
        if (!data.items.length) {
            threadsHtml = '<div class="forum-empty">No threads yet. Be the first to post!</div>';
        } else {
            threadsHtml = `
                <div class="forum-threads-wrap">
                    ${data.items.map(t => `
                        <a class="forum-thread-row" href="/forum/thread/${t.id}">
                            <img class="forum-thread-avatar" src="${escapeHtml(t.author_avatar)}" alt="" onerror="this.style.display='none'">
                            <div class="forum-thread-info">
                                <div class="forum-thread-title">
                                    ${t.is_pinned ? '<span class="forum-icon forum-icon-pin" title="Pinned">&#128204;</span>' : ''}
                                    ${t.is_locked ? '<span class="forum-icon forum-icon-lock" title="Locked">&#128274;</span>' : ''}
                                    <span>${escapeHtml(t.title)}</span>
                                </div>
                                <div class="forum-thread-sub">by ${escapeHtml(t.author_name)} &middot; ${timeAgo(t.created_at)}</div>
                            </div>
                            <div class="forum-thread-stats">
                                <div class="forum-thread-replies">${t.reply_count}</div>
                                <div class="forum-thread-time">${t.last_reply_at ? timeAgo(t.last_reply_at) : ''}</div>
                            </div>
                        </a>
                    `).join('')}
                </div>
            `;
        }

        // Pagination
        const totalPages = Math.ceil(data.total / data.per_page);
        let paginationHtml = '';
        if (totalPages > 1) {
            paginationHtml = '<div class="forum-pagination">';
            for (let i = 1; i <= totalPages; i++) {
                paginationHtml += `<a class="forum-page-btn ${i === page ? 'active' : ''}" href="#category/${escapeHtml(slug)}/${i}">${i}</a>`;
            }
            paginationHtml += '</div>';
        }

        content.innerHTML = `
            <div class="forum-thread-list-header">
                <h2>${escapeHtml(cat.name)}</h2>
                ${newThreadBtn}
            </div>
            ${newThreadForm}
            ${loginPrompt}
            ${threadsHtml}
            ${paginationHtml}
        `;
    } catch {
        content.innerHTML = '<div class="forum-empty">Failed to load threads.</div>';
    }
}

function toggleNewThread() {
    const form = document.getElementById('newThreadForm');
    if (form) form.classList.toggle('visible');
}

async function submitNewThread(slug) {
    const title = document.getElementById('threadTitle').value.trim();
    const body = document.getElementById('threadBody').value.trim();
    const btn = document.getElementById('submitThread');

    if (!title || title.length < 3) return alert('Title must be at least 3 characters.');
    if (!body) return alert('Post body cannot be empty.');

    btn.disabled = true;
    btn.textContent = 'Posting...';

    try {
        const res = await fetch('/api/forum/threads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_slug: slug, title, body }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to create thread');
        }
        const data = await res.json();
        window.location.href = `/forum/thread/${data.id}`;
    } catch (e) {
        alert(e.message);
        btn.disabled = false;
        btn.textContent = 'Post Thread';
    }
}

// ── Router ──

async function handleRoute() {
    const route = getRoute();
    if (route.view === 'threads') {
        await renderThreads(route.slug, route.page);
    } else if (route.view === 'search') {
        await renderSearchResults(route.query, route.page);
    } else {
        await renderCategories();
    }
}

// ── Init ──

document.addEventListener('DOMContentLoaded', async () => {
    await fetchCurrentUser();
    await handleRoute();
    window.addEventListener('hashchange', handleRoute);
});
