/* ===== Streamer Profiles ===== */

const STREAMERS = [
    {
        name: "primekirbs",
        displayName: "primekirbs",
        avatar: "K",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/487fa4fe-9d71-4221-a9c3-328471effc03-profile_image-300x300.png",
        platform: "twitch",
        bio: "Hello, I am Kirbs! Ragnarok Online streamer from the Philippines.",
        socials: { twitch: "https://www.twitch.tv/primekirbs", facebook: "https://www.facebook.com/kirbsplays" }
    },
    {
        name: "andzph",
        displayName: "AndzPH",
        avatar: "A",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/4ebf3401-09b2-4a19-b20b-604e2f8f7fa3-profile_image-300x300.png",
        platform: "twitch",
        bio: "Andz is my name, Ragnarok is my game. Twitch Affiliate and PH RO content creator.",
        socials: { twitch: "https://www.twitch.tv/andzph" }
    },
    {
        name: "hakister",
        displayName: "hakister",
        avatar: "H",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/0ef15cdb-c361-45e4-bb93-ebbd396d3819-profile_image-300x300.png",
        platform: "twitch",
        bio: "Streaming programming stuff and games whenever I can. Twitch Affiliate.",
        socials: { twitch: "https://www.twitch.tv/hakister" }
    },
    {
        name: "xrhonn",
        displayName: "xRhonn",
        avatar: "R",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/62fa4e97-0c13-4482-b029-73c046addc65-profile_image-300x300.png",
        platform: "twitch",
        bio: "Twitch Affiliate streamer. Catch me on Twitch, Facebook, and TikTok!",
        socials: { twitch: "https://www.twitch.tv/xrhonn", facebook: "https://fb.gg/xrhonnn" }
    },
    {
        name: "apocalyptogg",
        displayName: "apocalyptoGG",
        avatar: "G",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/e611e3be-c657-487d-bb29-f5439f5fbb7d-profile_image-300x300.png",
        platform: "twitch",
        bio: "Expect Old School Ragnarok Online and Just Chatting with pop-rock-OPM songs.",
        socials: { twitch: "https://www.twitch.tv/apocalyptogg" }
    },
    {
        name: "bossnel29",
        displayName: "bossnel29",
        avatar: "N",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/eb14aebc-cb36-4c8b-9e3f-7e19b60da77d-profile_image-300x300.png",
        platform: "twitch",
        bio: "Ragnarok Online streamer and Twitch Affiliate from the Philippines.",
        socials: { twitch: "https://www.twitch.tv/bossnel29" }
    },
    {
        name: "arthrconan",
        displayName: "ArthrConan",
        avatar: "C",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/d581d145-49be-4c76-96de-b11d05342045-profile_image-300x300.png",
        platform: "twitch",
        bio: "Twitch Affiliate streamer.",
        socials: { twitch: "https://www.twitch.tv/arthrconan" }
    },
    {
        name: "tsinopuppy",
        displayName: "TsinoPuppy",
        avatar: "T",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/459ad349-4a8d-4560-a635-1062e16b76d9-profile_image-300x300.png",
        platform: "twitch",
        bio: "Gamer.",
        socials: { twitch: "https://www.twitch.tv/tsinopuppy" }
    },
    {
        name: "indeavori",
        displayName: "indeavori",
        avatar: "I",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/d20ecc59-da17-4ea4-8d9f-f4df67b88310-profile_image-300x300.png",
        platform: "twitch",
        bio: "I usually play Ragnarok Online and Apex Legends. Also does art commissions!",
        socials: { twitch: "https://www.twitch.tv/indeavori" }
    },
    {
        name: "john_weak_tv",
        displayName: "john_weak_tv",
        avatar: "J",
        avatarUrl: "https://static-cdn.jtvnw.net/jtv_user_pictures/235392cd-b88c-4cc8-b3d9-d76722116ac2-profile_image-300x300.jpeg",
        platform: "twitch",
        bio: "US Navy streamer. Your help is appreciated — please subscribe and share!",
        socials: { twitch: "https://www.twitch.tv/john_weak_tv" }
    },
    {
        name: "BossHooHoo",
        displayName: "Hoo Hoo",
        avatar: "H",
        avatarUrl: "https://yt3.ggpht.com/jJ-nO8hJbgQVbcJyUQBRmEz-COjmTa2hti_Ap23_ARbe9VEQkqsT0MbqpzQyozfLuI33eo0EXg=s800-c-k-c0x00ffffff-no-rj",
        platform: "youtube",
        bio: "I don't play games casually. It's either I'm not interested or play for 16 hours and forget to eat.",
        socials: { youtube: "https://www.youtube.com/@BossHooHoo" }
    }
];

/* ===== SVG Icons ===== */
const SOCIAL_ICONS = {
    facebook: '<svg viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
    youtube: '<svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    twitch: '<svg viewBox="0 0 24 24"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z"/></svg>'
};

/* ===== Utilities ===== */

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

const ALLOWED_PLATFORMS = ['twitch', 'youtube', 'facebook'];

function safePlatform(p) {
    return ALLOWED_PLATFORMS.includes(p) ? p : 'unknown';
}

/* ===== Render Functions ===== */

function renderLiveStreamCard(stream, index) {
    const parentDomain = window.location.hostname;
    const autoplay = index === 0 ? 1 : 0;
    const platform = safePlatform(stream.platform);
    const login = encodeURIComponent(stream.user_login || '');

    let embedSrc;
    let watchTitle;
    if (platform === 'youtube') {
        const videoId = encodeURIComponent(stream.video_id || '');
        embedSrc = `https://www.youtube.com/embed/${videoId}?autoplay=${autoplay}&mute=1`;
        watchTitle = 'Watch on YouTube';
    } else {
        embedSrc = `https://player.twitch.tv/?channel=${login}&parent=${parentDomain}&muted=true&autoplay=${autoplay ? 'true' : 'false'}`;
        watchTitle = 'Watch on Twitch';
    }

    const gameTag = stream.game ? `<span class="stream-game">${escapeHtml(stream.game)}</span>` : '';
    const platformTag = `<span class="stream-platform-tag platform-${platform}">${escapeHtml(platform)}</span>`;
    const channelUrl = escapeHtml(stream.channel_url || '#');

    return `
        <div class="stream-card stream-card-real">
            <div class="stream-embed stream-embed-real">
                <span class="stream-live-badge">LIVE</span>
                <iframe src="${embedSrc}"
                    frameborder="0" allowfullscreen="true"
                    allow="autoplay; encrypted-media"
                    style="width:100%;height:100%;border:none;"></iframe>
            </div>
            <div class="stream-info">
                <div class="stream-avatar">
                    <a href="${channelUrl}" target="_blank" rel="noopener" title="${watchTitle}">${escapeHtml(stream.streamer.charAt(0))}</a>
                </div>
                <div class="stream-meta">
                    <div class="stream-name">${escapeHtml(stream.streamer)} ${gameTag} ${platformTag}</div>
                    <div class="stream-title">${escapeHtml(stream.title)}</div>
                </div>
                <div class="stream-viewers">${stream.viewers.toLocaleString()} viewers</div>
            </div>
        </div>
    `;
}

function renderStreamerCard(streamer, liveData) {
    const isLive = !!liveData;
    const statusClass = isLive ? 'online' : '';
    const liveBadge = isLive ? '<span class="streamer-live-badge">LIVE</span>' : '';
    const viewers = isLive ? Number(liveData.viewers) || 0 : 0;
    const statusText = isLive
        ? `<div class="streamer-viewers-tag">${viewers.toLocaleString()} viewers</div>`
        : '<div class="streamer-viewers-tag offline-text">Offline</div>';

    const platform = safePlatform(streamer.platform);
    const avatarImg = streamer.avatarUrl
        ? `<img src="${escapeHtml(streamer.avatarUrl)}" alt="${escapeHtml(streamer.displayName)}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`
        : escapeHtml(streamer.avatar);

    const socialsHtml = Object.entries(streamer.socials).map(([p, url]) => `
        <a href="${escapeHtml(url)}" class="social-link" title="${escapeHtml(p)}" target="_blank" rel="noopener">
            ${SOCIAL_ICONS[p] || ''}
        </a>
    `).join('');

    return `
        <div class="streamer-card">
            <div class="streamer-header">
                ${liveBadge}
                <div class="streamer-avatar">
                    ${avatarImg}
                    <span class="streamer-status-dot ${statusClass}"></span>
                </div>
                <div>
                    <div class="streamer-name">${escapeHtml(streamer.displayName)}</div>
                    <span class="streamer-platform platform-${platform}">${escapeHtml(platform)}</span>
                </div>
            </div>
            <div class="streamer-body">
                <p class="streamer-bio">${escapeHtml(streamer.bio)}</p>
                ${statusText}
                <div class="streamer-socials">${socialsHtml}</div>
            </div>
        </div>
    `;
}

/* ===== Leaderboard ===== */

let _leaderboardEntries = [];
let _currentSort = 'hours';

function sortLeaderboard(metric) {
    _currentSort = metric;
    document.getElementById('sortHours').className = 'btn-toggle' + (metric === 'hours' ? ' active' : '');
    document.getElementById('sortStreams').className = 'btn-toggle' + (metric === 'streams' ? ' active' : '');
    document.getElementById('sortViews').className = 'btn-toggle' + (metric === 'views' ? ' active' : '');
    renderLeaderboardTable(_leaderboardEntries, metric);
}

function renderLeaderboardTable(entries, sortMetric) {
    const wrapper = document.getElementById('leaderboardWrapper');
    if (!wrapper) return;

    if (!entries || entries.length === 0) {
        wrapper.innerHTML = '<div class="leaderboard-empty">No leaderboard data available.</div>';
        return;
    }

    const keyMap = { hours: 'total_hours', streams: 'streams', views: 'total_views' };
    const key = keyMap[sortMetric] || 'total_hours';
    const sorted = [...entries].sort((a, b) => {
        const av = a[key] !== null && a[key] !== undefined ? a[key] : -1;
        const bv = b[key] !== null && b[key] !== undefined ? b[key] : -1;
        return bv - av;
    });

    const rowsHtml = sorted.map((entry, i) => {
        const rank = i + 1;
        const medal = rank === 1 ? '<span class="lb-medal gold">1</span>'
                    : rank === 2 ? '<span class="lb-medal silver">2</span>'
                    : rank === 3 ? '<span class="lb-medal bronze">3</span>'
                    : `<span class="lb-rank-num">#${rank}</span>`;
        const platform = safePlatform(entry.platform);

        const avatarHtml = entry.avatar_url
            ? `<img src="${escapeHtml(entry.avatar_url)}" alt="${escapeHtml(entry.name)}" class="lb-avatar-img" onerror="this.style.display='none'">`
            : '';

        const streamsCell = entry.streams !== null && entry.streams !== undefined
            ? entry.streams.toLocaleString()
            : '<span class="lb-na">—</span>';

        const hoursCell = entry.total_hours !== null && entry.total_hours !== undefined
            ? `${entry.total_hours.toLocaleString(undefined, {maximumFractionDigits: 1})}h`
            : '<span class="lb-na">—</span>';

        const viewsCell = entry.total_views !== null && entry.total_views !== undefined
            ? entry.total_views.toLocaleString()
            : '<span class="lb-na">—</span>';

        const sourceLabel = entry.data_source === 'youtube_channel_stats'
            ? '<span class="lb-source-tag">Channel Stats</span>'
            : '';

        const channelUrl = escapeHtml(entry.channel_url || '#');

        return `<tr class="lb-row ${rank <= 3 ? 'lb-row-top' : ''}">
            <td class="lb-col-rank">${medal}</td>
            <td class="lb-col-name">
                <div class="lb-name-cell">
                    <div class="lb-avatar">${avatarHtml}<span class="lb-avatar-placeholder">${escapeHtml(entry.name.charAt(0))}</span></div>
                    <div>
                        <a href="${channelUrl}" target="_blank" rel="noopener" class="lb-name-link">${escapeHtml(entry.name)}</a>
                        <span class="lb-platform-tag platform-${platform}">${escapeHtml(platform)}</span>
                        ${sourceLabel}
                    </div>
                </div>
            </td>
            <td class="lb-col-stat ${sortMetric === 'streams' ? 'lb-active-col' : ''}">${streamsCell}</td>
            <td class="lb-col-stat ${sortMetric === 'hours' ? 'lb-active-col' : ''}">${hoursCell}</td>
            <td class="lb-col-stat ${sortMetric === 'views' ? 'lb-active-col' : ''}">${viewsCell}</td>
        </tr>`;
    }).join('');

    wrapper.innerHTML = `
        <div class="leaderboard-table-wrap">
            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th class="lb-col-rank">Rank</th>
                        <th class="lb-col-name">Streamer</th>
                        <th class="lb-col-stat ${sortMetric === 'streams' ? 'lb-active-col' : ''}">Streams</th>
                        <th class="lb-col-stat ${sortMetric === 'hours' ? 'lb-active-col' : ''}">Hours</th>
                        <th class="lb-col-stat ${sortMetric === 'views' ? 'lb-active-col' : ''}">Views</th>
                    </tr>
                </thead>
                <tbody>${rowsHtml}</tbody>
            </table>
        </div>`;
}

async function fetchLeaderboard() {
    try {
        const resp = await fetch('/api/leaderboard');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        _leaderboardEntries = data.entries || [];

        const subtitle = document.getElementById('leaderboardSubtitle');
        if (subtitle && data.month) {
            const [yr, mo] = data.month.split('-');
            const label = new Date(yr, mo - 1, 1).toLocaleString('default', { month: 'long', year: 'numeric' });
            subtitle.textContent = `VOD stats for ${label}`;
        }

        const loading = document.getElementById('leaderboardLoading');
        if (loading) loading.style.display = 'none';

        const controls = document.getElementById('leaderboardControls');
        if (controls) controls.style.display = 'flex';

        renderLeaderboardTable(_leaderboardEntries, _currentSort);
    } catch (e) {
        const wrapper = document.getElementById('leaderboardWrapper');
        if (wrapper) wrapper.innerHTML = '<div class="leaderboard-empty">Could not load leaderboard. Please try again later.</div>';
    }
}

/* ===== Initialize on Page Load ===== */
document.addEventListener('DOMContentLoaded', () => {
    const streamsGrid = document.getElementById('streamsGrid');
    const streamersGrid = document.getElementById('streamersGrid');
    const allStreamersGrid = document.getElementById('allStreamersGrid');

    const POLL_INTERVAL = 60000; /* 60 seconds — matches backend cache TTL */

    /* Shared live data */
    let liveStreams = [];
    let prevLiveKey = ''; /* fingerprint to detect changes */

    async function fetchLiveStreams() {
        try {
            const resp = await fetch('/api/live-streams');
            const data = await resp.json();
            if (data.streams) liveStreams = data.streams;
        } catch (e) { /* API unavailable */ }
    }

    function getLiveData(username) {
        return liveStreams.find(s => s.user_login.toLowerCase() === username.toLowerCase()) || null;
    }

    /* Build a fingerprint of current live state to detect changes */
    function liveFingerprint() {
        return liveStreams.map(s => `${s.platform}:${s.user_login}`).sort().join(',');
    }

    /* Sort streamers alphabetically (stable, computed once) */
    const sorted = [...STREAMERS].sort((a, b) => a.displayName.localeCompare(b.displayName, undefined, { sensitivity: 'base' }));

    function renderStreamerSections() {
        /* Landing page: show first 6 streamer profiles with live status */
        if (streamersGrid) {
            streamersGrid.innerHTML = sorted.slice(0, 6).map(s => renderStreamerCard(s, getLiveData(s.name))).join('');
        }

        /* Full streamers page: show all with live status */
        if (allStreamersGrid) {
            allStreamersGrid.innerHTML = sorted.map(s => renderStreamerCard(s, getLiveData(s.name))).join('');

            const countEl = document.getElementById('streamerCount');
            if (countEl) {
                const online = sorted.filter(s => getLiveData(s.name)).length;
                countEl.textContent = `${STREAMERS.length} streamers — ${online} currently live`;
            }
        }
    }

    function renderLiveSection() {
        if (!streamsGrid) return;
        if (liveStreams.length > 0) {
            streamsGrid.innerHTML = liveStreams.map((s, i) => renderLiveStreamCard(s, i)).join('');
            initCarousel(streamsGrid);
        } else {
            streamsGrid.innerHTML = '<div class="empty-streams">No streamers are live right now. Check back later!</div>';
        }
    }

    /* Initial load */
    async function init() {
        await fetchLiveStreams();
        prevLiveKey = liveFingerprint();
        renderLiveSection();
        renderStreamerSections();

        /* Start polling */
        setInterval(poll, POLL_INTERVAL);
    }

    /* Poll for changes — only re-render when live lineup changes */
    async function poll() {
        await fetchLiveStreams();
        const newKey = liveFingerprint();
        if (newKey !== prevLiveKey) {
            prevLiveKey = newKey;
            renderLiveSection();
            renderStreamerSections();
        }
    }

    init();

    /* Leaderboard sort buttons */
    const sortHoursBtn = document.getElementById('sortHours');
    const sortStreamsBtn = document.getElementById('sortStreams');
    const sortViewsBtn = document.getElementById('sortViews');
    if (sortHoursBtn) sortHoursBtn.addEventListener('click', () => sortLeaderboard('hours'));
    if (sortStreamsBtn) sortStreamsBtn.addEventListener('click', () => sortLeaderboard('streams'));
    if (sortViewsBtn) sortViewsBtn.addEventListener('click', () => sortLeaderboard('views'));

    /* Fetch leaderboard if on streamers page */
    if (document.getElementById('leaderboardWrapper')) {
        fetchLeaderboard();
    }

    /* Carousel scroll buttons */
    function initCarousel(track) {
        const prevBtn = document.getElementById('streamsPrev');
        const nextBtn = document.getElementById('streamsNext');
        if (!prevBtn || !nextBtn) return;

        const scrollAmount = 340;

        function updateButtons() {
            prevBtn.disabled = track.scrollLeft <= 0;
            nextBtn.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
        }

        prevBtn.addEventListener('click', () => {
            track.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        nextBtn.addEventListener('click', () => {
            track.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        track.addEventListener('scroll', updateButtons);
        updateButtons();
    }
});
