/* Dark mode toggle — persisted via localStorage */
(function() {
    // Apply saved theme immediately to prevent flash
    var saved = localStorage.getItem('theme');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');

    document.addEventListener('DOMContentLoaded', function() {
        var btn = document.createElement('button');
        btn.className = 'dark-mode-toggle';
        btn.setAttribute('aria-label', 'Toggle dark mode');
        btn.title = 'Toggle dark mode';
        updateIcon(btn);

        // Append to nav if available, otherwise to body
        var nav = document.querySelector('.site-nav');
        if (nav) {
            nav.appendChild(btn);
        } else {
            document.body.appendChild(btn);
        }

        btn.addEventListener('click', function() {
            var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDark) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
            updateIcon(btn);
        });
    });

    function updateIcon(btn) {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        btn.textContent = isDark ? '\u2600' : '\uD83C\uDF19';
    }
})();
