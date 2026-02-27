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
    },
    {
        name: "CrusaderBlade",
        avatar: "C",
        platform: "facebook",
        isOnline: true,
        viewers: 278,
        streamTitle: "Grand Cross Crusader — Bio3 Solo Runs",
        bio: "Paladin / Royal Guard main. I love tanking, Grand Cross builds, and soloing instances for the community.",
        socials: { facebook: "#", youtube: "#" }
    },
    {
        name: "DancerMuse",
        avatar: "D",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Dancer / Gypsy support player. I stream party play, WoE support tactics, and fun meme builds.",
        socials: { youtube: "#" }
    },
    {
        name: "AssassinCross_PH",
        avatar: "A",
        platform: "facebook",
        isOnline: true,
        viewers: 415,
        streamTitle: "SBK Farming — Zeny Grind Session",
        bio: "Assassin Cross main since classic RO. Soul Breaker PvP and efficient farming streams daily.",
        socials: { facebook: "#", youtube: "#" }
    },
    {
        name: "MonkFistPH",
        avatar: "F",
        platform: "twitch",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Champion / Sura enthusiast. Asura Strike one-shots, combo monk builds, and PvP highlights.",
        socials: { twitch: "#", facebook: "#" }
    },
    {
        name: "AlchemistLab",
        avatar: "L",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Biochemist / Geneticist main. Homunculus guides, Hell Plant builds, and crafting economy tips.",
        socials: { youtube: "#" }
    },
    {
        name: "BardOfGeffen",
        avatar: "G",
        platform: "facebook",
        isOnline: true,
        viewers: 156,
        streamTitle: "Maestro Support — WoE Guild Runs",
        bio: "Bard / Maestro player focused on WoE ensemble support. Music buffs and party coordination streams.",
        socials: { facebook: "#", youtube: "#" }
    },
    {
        name: "NinjaShadowPH",
        avatar: "N",
        platform: "facebook",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Ninja / Kagerou main. Showcasing the underrated ninja class with unique PvP and PvM builds.",
        socials: { facebook: "#" }
    },
    {
        name: "GunSlingerAce",
        avatar: "R",
        platform: "twitch",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Gunslinger / Rebellion specialist. Rapid fire builds, coin flip strategies, and Western-themed streams.",
        socials: { twitch: "#", youtube: "#" }
    },
    {
        name: "SuperNovicePH",
        avatar: "V",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Super Novice challenge runner. Can a Super Novice clear ET? Tune in and find out. Meme builds welcome.",
        socials: { youtube: "#", facebook: "#" }
    },
    {
        name: "TaeKwonMaster",
        avatar: "T",
        platform: "facebook",
        isOnline: true,
        viewers: 203,
        streamTitle: "Star Gladiator PvP — Ranked Matches",
        bio: "Star Gladiator / Soul Linker duo player. Kick combos, universe stance PvP, and soul link support.",
        socials: { facebook: "#" }
    },
    {
        name: "SageElemental",
        avatar: "E",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Professor / Sorcerer main. Elemental strategy, spell combos, and endgame magic DPS optimization.",
        socials: { youtube: "#", facebook: "#" }
    },
    {
        name: "BlacksmithForge",
        avatar: "X",
        platform: "facebook",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Whitesmith / Mechanic crafter. Forging success streams, cart builds, and merchant class economy guides.",
        socials: { facebook: "#", youtube: "#" }
    },
    {
        name: "RogueLifePH",
        avatar: "O",
        platform: "twitch",
        isOnline: true,
        viewers: 189,
        streamTitle: "Rogue Treasure Hunting — Gramps Party",
        bio: "Rogue / Shadow Chaser treasure hunter. Plagiarism builds, steal farming, and fun party content.",
        socials: { twitch: "#", facebook: "#" }
    },
    {
        name: "PetAdventures",
        avatar: "J",
        platform: "youtube",
        isOnline: false,
        viewers: 0,
        streamTitle: "",
        bio: "Pet system enthusiast and casual player. Taming guides, pet evolution, and wholesome RO adventures.",
        socials: { youtube: "#", facebook: "#" }
    }
];

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
    const allStreamersGrid = document.getElementById('allStreamersGrid');

    if (streamsGrid) {
        loadLiveStreams(streamsGrid);
    }

    /* Fetch real live streams from backend, then combine with dummy online streamers */
    async function loadLiveStreams(grid) {
        const onlineStreamers = STREAMERS.filter(s => s.isOnline);

        let realHtml = '';
        try {
            const resp = await fetch('/api/live-streams');
            const data = await resp.json();
            if (data.streams && data.streams.length > 0) {
                realHtml = data.streams.map(renderLiveStreamCard).join('');
            }
        } catch (e) {
            /* API unavailable — just show dummy streams */
        }

        const dummyHtml = onlineStreamers.map(renderStreamCard).join('');
        const combined = realHtml + dummyHtml;

        if (combined) {
            grid.innerHTML = combined;
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

    /* Landing page: show first 6 streamers */
    if (streamersGrid) {
        const sorted = [...STREAMERS].sort((a, b) => b.isOnline - a.isOnline || b.viewers - a.viewers);
        streamersGrid.innerHTML = sorted.slice(0, 6).map(renderStreamerCard).join('');
    }

    /* Full streamers page: show all */
    if (allStreamersGrid) {
        const sorted = [...STREAMERS].sort((a, b) => b.isOnline - a.isOnline || b.viewers - a.viewers);
        allStreamersGrid.innerHTML = sorted.map(renderStreamerCard).join('');

        /* Update count */
        const countEl = document.getElementById('streamerCount');
        if (countEl) {
            const online = STREAMERS.filter(s => s.isOnline).length;
            countEl.textContent = `${STREAMERS.length} streamers — ${online} currently live`;
        }
    }
});
