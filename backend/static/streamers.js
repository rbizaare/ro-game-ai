/* ===== Streamer Placeholder Data & Rendering ===== */

const STREAMERS = [
    {
        name: "KnightWalker",
        avatar: "K",
        platform: "facebook",
        isOnline: true,
        viewers: 342,
        streamTitle: "WoE Practice — Guild Siege Highlights!",
        bio: "Veteran RO player since 2003. Lord Knight main specializing in WoE and MVP hunts. Streams guild wars every weekend.",
        socials: { facebook: "#", youtube: "#" }
    },
    {
        name: "PriestlyHeals",
        avatar: "P",
        platform: "youtube",
        isOnline: true,
        viewers: 187,
        streamTitle: "Full Support HP — ET Floor 90+ Runs",
        bio: "High Priest / Arch Bishop main. I stream party content, Endless Tower runs, and new player guides.",
        socials: { youtube: "#", facebook: "#" }
    },
    {
        name: "ShadowChaser_PH",
        avatar: "S",
        platform: "facebook",
        isOnline: true,
        viewers: 521,
        streamTitle: "BG Ranked Matches — Road to Top 10",
        bio: "Stalker / Shadow Chaser PvP specialist. If it involves stealth and strategy, I'm in. Daily BG streams.",
        socials: { facebook: "#" }
    },
    {
        name: "BrewerMaster",
        avatar: "B",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Creator class enthusiast. Potion brewing, homunculus guides, and merchant life content.",
        socials: { youtube: "#", facebook: "#" }
    },
    {
        name: "MVPHunterX",
        avatar: "M",
        platform: "twitch",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Sniper main doing daily MVP hunts and farming guides. I share all my zeny-making secrets.",
        socials: { twitch: "#", youtube: "#" }
    },
    {
        name: "WizardOfProntera",
        avatar: "W",
        platform: "facebook",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "High Wizard / Warlock PvM player. AoE farming, leveling guides, and chill grinding sessions.",
        socials: { facebook: "#", youtube: "#" }
    }
];

/* ===== SVG Icons ===== */
const SOCIAL_ICONS = {
    facebook: '<svg viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
    youtube: '<svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    twitch: '<svg viewBox="0 0 24 24"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z"/></svg>'
};

/* ===== Render Functions ===== */

function renderStreamCard(streamer) {
    return `
        <div class="stream-card">
            <div class="stream-embed">
                <span class="stream-live-badge">LIVE</span>
                <span>Stream Preview</span>
            </div>
            <div class="stream-info">
                <div class="stream-avatar">${streamer.avatar}</div>
                <div class="stream-meta">
                    <div class="stream-name">${streamer.name}</div>
                    <div class="stream-title">${streamer.streamTitle}</div>
                </div>
                <div class="stream-viewers">${streamer.viewers} viewers</div>
            </div>
        </div>
    `;
}

function renderStreamerCard(streamer) {
    const statusClass = streamer.isOnline ? 'online' : '';
    const statusText = streamer.isOnline
        ? `<div class="streamer-viewers-tag">${streamer.viewers} viewers — LIVE</div>`
        : '<div class="streamer-viewers-tag offline-text">Offline</div>';

    const socialsHtml = Object.entries(streamer.socials).map(([platform, url]) => `
        <a href="${url}" class="social-link" title="${platform}">
            ${SOCIAL_ICONS[platform] || ''}
        </a>
    `).join('');

    return `
        <div class="streamer-card">
            <div class="streamer-header">
                <div class="streamer-avatar">
                    ${streamer.avatar}
                    <span class="streamer-status-dot ${statusClass}"></span>
                </div>
                <div>
                    <div class="streamer-name">${streamer.name}</div>
                    <span class="streamer-platform platform-${streamer.platform}">${streamer.platform}</span>
                </div>
            </div>
            <div class="streamer-body">
                <p class="streamer-bio">${streamer.bio}</p>
                ${statusText}
                <div class="streamer-socials">${socialsHtml}</div>
            </div>
        </div>
    `;
}

/* ===== Initialize on Page Load ===== */
document.addEventListener('DOMContentLoaded', () => {
    const streamsGrid = document.getElementById('streamsGrid');
    const streamersGrid = document.getElementById('streamersGrid');

    if (streamsGrid) {
        const onlineStreamers = STREAMERS.filter(s => s.isOnline);
        if (onlineStreamers.length > 0) {
            streamsGrid.innerHTML = onlineStreamers.map(renderStreamCard).join('');
            initCarousel(streamsGrid);
        } else {
            streamsGrid.innerHTML = '<div class="empty-streams">No streamers are live right now. Check back later!</div>';
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

    if (streamersGrid) {
        const sorted = [...STREAMERS].sort((a, b) => b.isOnline - a.isOnline || b.viewers - a.viewers);
        streamersGrid.innerHTML = sorted.map(renderStreamerCard).join('');
    }
});
