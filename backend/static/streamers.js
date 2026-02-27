/* ===== SVG Icons ===== */
const SOCIAL_ICONS = {
    facebook: '<svg viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
    youtube: '<svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    twitch: '<svg viewBox="0 0 24 24"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z"/></svg>'
};

/* ===== Render Functions ===== */

function renderLiveStreamCard(stream) {
    const parentDomain = window.location.hostname;
    const embedSrc = `https://player.twitch.tv/?channel=${stream.user_login}&parent=${parentDomain}&muted=true&autoplay=true`;
    const gameTag = stream.game ? `<span class="stream-game">${stream.game}</span>` : '';
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
                    <a href="${stream.channel_url}" target="_blank" rel="noopener" title="Watch on Twitch">${stream.streamer.charAt(0)}</a>
                </div>
                <div class="stream-meta">
                    <div class="stream-name">${stream.streamer} ${gameTag}</div>
                    <div class="stream-title">${stream.title}</div>
                </div>
                <div class="stream-viewers">${stream.viewers.toLocaleString()} viewers</div>
            </div>
        </div>
    `;
}

/* ===== Initialize on Page Load ===== */
document.addEventListener('DOMContentLoaded', () => {
    const streamsGrid = document.getElementById('streamsGrid');

    if (streamsGrid) {
        loadLiveStreams(streamsGrid);
    }

    /* Fetch real live streams from Twitch API */
    async function loadLiveStreams(grid) {
        let streams = [];
        try {
            const resp = await fetch('/api/live-streams');
            const data = await resp.json();
            if (data.streams && data.streams.length > 0) {
                streams = data.streams;
            }
        } catch (e) {
            /* API unavailable */
        }

        if (streams.length > 0) {
            grid.innerHTML = streams.map(renderLiveStreamCard).join('');
            initCarousel(grid);
        } else {
            grid.innerHTML = '<div class="empty-streams">No streamers are live right now. Check back later!</div>';
        }
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
