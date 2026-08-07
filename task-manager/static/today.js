(function () {
    "use strict";

    function initTodayDrawer() {
        var layer = document.getElementById("today-drawer-layer");
        var drawer = document.getElementById("today-detail-drawer");
        var closeButton = layer && layer.querySelector("[data-today-drawer-close].today-detail-close");
        var title = document.getElementById("today-detail-title");
        var context = document.getElementById("today-detail-context");
        var status = document.getElementById("today-detail-status");
        var priority = document.getElementById("today-detail-priority");
        var meta = document.getElementById("today-detail-meta");
        var tag = document.getElementById("today-detail-tag");
        var lastTrigger = null;
        var closeTimer = null;

        if (!layer || !drawer || !closeButton) {
            return;
        }

        function openDrawer(trigger) {
            lastTrigger = trigger;
            title.textContent = trigger.dataset.title || "任务详情";
            context.textContent = trigger.dataset.context || "Today 工作台";
            status.textContent = trigger.dataset.status || "待办";
            status.className = "today-detail-status today-detail-status-" + (trigger.dataset.status === "已完成" ? "done" : "todo");
            priority.textContent = trigger.dataset.priority || "未设置";
            priority.className = "today-detail-priority today-detail-priority-" + (trigger.dataset.priorityClass || "low");
            meta.textContent = trigger.dataset.meta || "暂无截止时间";
            tag.textContent = trigger.dataset.tag || "未分类";

            if (closeTimer) {
                window.clearTimeout(closeTimer);
            }
            layer.hidden = false;
            document.body.classList.add("today-drawer-open");
            window.requestAnimationFrame(function () {
                drawer.classList.add("is-open");
            });
            closeButton.focus();
        }

        function closeDrawer() {
            drawer.classList.remove("is-open");
            document.body.classList.remove("today-drawer-open");
            closeTimer = window.setTimeout(function () {
                layer.hidden = true;
            }, 220);
            if (lastTrigger) {
                lastTrigger.focus();
            }
        }

        document.querySelectorAll("[data-today-detail]").forEach(function (trigger) {
            trigger.addEventListener("click", function () {
                openDrawer(trigger);
            });
        });

        layer.querySelectorAll("[data-today-drawer-close]").forEach(function (button) {
            button.addEventListener("click", closeDrawer);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !layer.hidden) {
                closeDrawer();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initTodayDrawer);
    } else {
        initTodayDrawer();
    }
})();
