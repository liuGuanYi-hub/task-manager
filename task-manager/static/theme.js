(function () {
    "use strict";

    var MODE_KEY = "task-manager-theme-mode";
    var ACCENT_KEY = "task-manager-theme-accent";
    var modes = ["system", "light", "dark"];
    var accents = ["default", "rose", "ocean", "mint"];
    var modeLabels = {
        system: "跟随系统",
        light: "浅色",
        dark: "深色"
    };
    var accentLabels = {
        "default": "蓝紫",
        rose: "玫红",
        ocean: "海洋",
        mint: "薄荷"
    };

    function read(key, fallback, validValues) {
        try {
            var value = window.localStorage.getItem(key);
            return validValues.indexOf(value) >= 0 ? value : fallback;
        } catch (error) {
            return fallback;
        }
    }

    function write(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (error) {
            // 隐私模式或浏览器禁用存储时，主题仍在当前页面生效。
        }
    }

    var currentMode = read(MODE_KEY, "system", modes);
    var currentAccent = read(ACCENT_KEY, "default", accents);

    function applyMode(mode, persist) {
        currentMode = modes.indexOf(mode) >= 0 ? mode : "system";
        document.documentElement.dataset.theme = currentMode;
        if (persist) {
            write(MODE_KEY, currentMode);
        }

        var status = document.getElementById("theme-status");
        if (status) {
            status.textContent = modeLabels[currentMode];
        }
        document.querySelectorAll("[data-theme-mode]").forEach(function (button) {
            var active = button.dataset.themeMode === currentMode;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });
    }

    function applyAccent(accent, persist) {
        currentAccent = accents.indexOf(accent) >= 0 ? accent : "default";
        document.documentElement.dataset.accent = currentAccent;
        if (persist) {
            write(ACCENT_KEY, currentAccent);
        }
        document.querySelectorAll("[data-accent]").forEach(function (button) {
            var active = button.dataset.accent === currentAccent;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        var accentStatus = document.getElementById("theme-accent-status");
        if (accentStatus) {
            accentStatus.textContent = accentLabels[currentAccent] + "主题";
        }
    }

    // 在样式表加载前设置 data 属性，减少首次渲染时的主题闪烁。
    applyMode(currentMode, false);
    applyAccent(currentAccent, false);

    function bindControls() {
        document.querySelectorAll("[data-theme-mode]").forEach(function (button) {
            button.addEventListener("click", function () {
                applyMode(button.dataset.themeMode, true);
            });
        });
        document.querySelectorAll("[data-accent]").forEach(function (button) {
            button.addEventListener("click", function () {
                applyAccent(button.dataset.accent, true);
            });
        });

        var toggle = document.getElementById("theme-toggle");
        if (toggle) {
            toggle.addEventListener("click", function () {
                var nextIndex = (modes.indexOf(currentMode) + 1) % modes.length;
                applyMode(modes[nextIndex], true);
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindControls);
    } else {
        bindControls();
    }

    if (window.matchMedia) {
        var media = window.matchMedia("(prefers-color-scheme: dark)");
        var handleSystemChange = function () {
            if (currentMode === "system") {
                applyMode(currentMode, false);
            }
        };
        if (media.addEventListener) {
            media.addEventListener("change", handleSystemChange);
        } else if (media.addListener) {
            media.addListener(handleSystemChange);
        }
    }
})();
