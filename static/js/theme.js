/**
 * 暗黑模式切换模块
 */

const DARK_MODE_KEY = 'twitter-downloader-dark-mode';

// 获取当前模式
function isDarkMode() {
    return localStorage.getItem(DARK_MODE_KEY) === 'true';
}

// 切换模式
function toggleDarkMode() {
    const dark = !isDarkMode();
    localStorage.setItem(DARK_MODE_KEY, dark);
    applyDarkMode(dark);
}

// 应用模式
function applyDarkMode(dark) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    // 更新切换按钮图标
    const btn = document.getElementById('theme-toggle');
    if (btn) {
        btn.innerHTML = dark ? getSunIcon() : getMoonIcon();
    }
}

// 太阳图标（亮色模式）
function getSunIcon() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="5"/>
        <path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
    </svg>`;
}

// 月亮图标（暗黑模式）
function getMoonIcon() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
    </svg>`;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    applyDarkMode(isDarkMode());
});

// 导出
window.themeModule = {
    isDarkMode,
    toggleDarkMode,
    applyDarkMode
};