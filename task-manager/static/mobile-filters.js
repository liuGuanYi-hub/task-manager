(function () {
    "use strict";

    function initMobileFilters() {
        const panel = document.querySelector("[data-mobile-filter-panel]");
        const trigger = document.querySelector("[data-mobile-filter-open]");
        const backdrop = document.querySelector(".mobile-filter-backdrop");
        if (!panel || !trigger || !backdrop) return;

        let closeTimer = null;
        document.body.classList.add("mobile-filter-ready");

        function openPanel() {
            window.clearTimeout(closeTimer);
            backdrop.hidden = false;
            document.body.classList.add("mobile-filter-open");
            panel.classList.add("is-open");
            trigger.setAttribute("aria-expanded", "true");
            const firstControl = panel.querySelector("select, input, button");
            if (firstControl) window.setTimeout(function () { firstControl.focus(); }, 30);
        }

        function closePanel() {
            document.body.classList.remove("mobile-filter-open");
            panel.classList.remove("is-open");
            trigger.setAttribute("aria-expanded", "false");
            window.clearTimeout(closeTimer);
            closeTimer = window.setTimeout(function () {
                if (!panel.classList.contains("is-open")) backdrop.hidden = true;
            }, 180);
            trigger.focus();
        }

        trigger.addEventListener("click", openPanel);
        document.querySelectorAll("[data-mobile-filter-close]").forEach(function (button) {
            button.addEventListener("click", closePanel);
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && document.body.classList.contains("mobile-filter-open")) {
                event.preventDefault();
                closePanel();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initMobileFilters);
    } else {
        initMobileFilters();
    }
})();
