/* Shared utilities — loaded before all other scripts */

function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}

function timeAgo(iso) {
    if (!iso) return '';
    var diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 2592000) return Math.floor(diff / 86400) + 'd ago';
    return new Date(iso).toLocaleDateString();
}

/* ── Toast notifications ── */
(function () {
    var container = null;

    function getContainer() {
        if (container) return container;
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }

    window.showToast = function (message, type, duration) {
        type = type || 'info';
        duration = duration || 3500;

        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;

        var c = getContainer();
        c.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(function () {
            toast.classList.add('toast-show');
        });

        setTimeout(function () {
            toast.classList.remove('toast-show');
            toast.classList.add('toast-hide');
            setTimeout(function () {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 300);
        }, duration);
    };
})();
