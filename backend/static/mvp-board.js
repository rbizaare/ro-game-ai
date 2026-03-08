/* Weekly MVP Board — top contributors and best thread */
(function () {
    var board = document.getElementById('mvpBoard');
    if (!board) return;

    var medals = ['&#x1F947;', '&#x1F948;', '&#x1F949;', '4', '5'];

    function renderForumMvps(mvps) {
        if (!mvps || mvps.length === 0) {
            return '<div class="mvp-panel">' +
                '<h4 class="mvp-panel-title">Forum MVPs</h4>' +
                '<p class="mvp-empty">No forum activity this week yet.</p>' +
            '</div>';
        }

        var rows = mvps.map(function (m, i) {
            var avatarHtml = m.avatar_url
                ? '<img src="' + escapeHtml(m.avatar_url) + '" class="shoutbox-avatar-img" alt="">'
                : '<span class="shoutbox-avatar-placeholder">' + escapeHtml(m.display_name.charAt(0).toUpperCase()) + '</span>';

            return '<tr class="lb-row">' +
                '<td class="lb-col-rank">' + medals[i] + '</td>' +
                '<td class="lb-col-name"><div class="lb-name-cell">' +
                    '<div class="shoutbox-avatar">' + avatarHtml + '</div>' +
                    '<div><a href="/forum/profile/' + m.user_id + '" class="lb-name-link">' + escapeHtml(m.display_name) + '</a>' +
                    '<br><span class="rank-badge">' + escapeHtml(m.rank_title) + '</span></div>' +
                '</div></td>' +
                '<td class="lb-col-stat">' + m.post_count + ' posts</td>' +
            '</tr>';
        }).join('');

        return '<div class="mvp-panel">' +
            '<h4 class="mvp-panel-title">Forum MVPs</h4>' +
            '<table class="leaderboard-table"><tbody>' + rows + '</tbody></table>' +
        '</div>';
    }

    function renderStreamerMvp(streamer) {
        if (!streamer) {
            return '<div class="mvp-panel">' +
                '<h4 class="mvp-panel-title">Top Streamer</h4>' +
                '<p class="mvp-empty">No streamer data this month.</p>' +
            '</div>';
        }

        var avatarHtml = streamer.avatar_url
            ? '<img src="' + escapeHtml(streamer.avatar_url) + '" class="mvp-streamer-avatar" alt="">'
            : '<div class="mvp-streamer-avatar-placeholder">&#127918;</div>';

        var platform = streamer.platform || '';
        var platformClass = platform === 'twitch' ? 'twitch' : 'youtube';

        return '<div class="mvp-panel">' +
            '<h4 class="mvp-panel-title">Top Streamer</h4>' +
            '<div class="mvp-streamer-card">' +
                avatarHtml +
                '<div class="mvp-streamer-info">' +
                    '<a href="' + escapeHtml(streamer.channel_url || '#') + '" target="_blank" class="mvp-streamer-name">' + escapeHtml(streamer.name) + '</a>' +
                    '<span class="lb-platform-tag ' + platformClass + '">' + escapeHtml(platform) + '</span>' +
                    '<div class="mvp-streamer-stat">' +
                        (streamer.total_hours != null ? escapeHtml(String(streamer.total_hours)) + 'h streamed' : escapeHtml(String(streamer.total_views || 0)) + ' views') +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
    }

    function renderBestThread(thread) {
        if (!thread) {
            return '<div class="mvp-panel">' +
                '<h4 class="mvp-panel-title">Best Thread</h4>' +
                '<p class="mvp-empty">No threads this week yet.</p>' +
            '</div>';
        }

        var avatarHtml = thread.author_avatar
            ? '<img src="' + escapeHtml(thread.author_avatar) + '" class="shoutbox-avatar-img" alt="">'
            : '<span class="shoutbox-avatar-placeholder">' + escapeHtml(thread.author_name.charAt(0).toUpperCase()) + '</span>';

        return '<div class="mvp-panel">' +
            '<h4 class="mvp-panel-title">Best Thread</h4>' +
            '<div class="mvp-thread-card">' +
                '<a href="/forum/thread/' + thread.id + '" class="mvp-thread-title">' + escapeHtml(thread.title) + '</a>' +
                '<div class="mvp-thread-meta">' +
                    '<div class="shoutbox-avatar" style="width:28px;height:28px;">' + avatarHtml + '</div>' +
                    '<span>' + escapeHtml(thread.author_name) + '</span>' +
                    '<span class="mvp-thread-replies">' + thread.reply_count + ' replies</span>' +
                '</div>' +
            '</div>' +
        '</div>';
    }

    // Fetch MVP board data
    fetch('/api/forum/mvp-board')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            board.innerHTML =
                renderForumMvps(data.forum_mvps) +
                renderStreamerMvp(data.streamer_mvp) +
                renderBestThread(data.best_thread);
        })
        .catch(function () {
            board.innerHTML = '<p class="mvp-empty">Could not load MVP board.</p>';
        });

    // Fetch top streamer from leaderboard
    fetch('/api/leaderboard')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var entries = data.entries || [];
            if (entries.length > 0) {
                var top = entries[0];
                // Update the streamer MVP panel
                var panel = board.querySelectorAll('.mvp-panel')[1];
                if (panel) {
                    panel.outerHTML = renderStreamerMvp(top);
                }
            }
        })
        .catch(function () { /* leaderboard unavailable, keep empty */ });
})();
