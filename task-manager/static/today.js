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
        var project = document.getElementById("today-detail-project");
        var tag = document.getElementById("today-detail-tag");
        var description = document.getElementById("today-detail-description");
        var updated = document.getElementById("today-detail-updated");
        var editLink = document.getElementById("today-detail-edit-link");
        var form = document.getElementById("today-detail-form");
        var titleInput = document.getElementById("today-detail-title-input");
        var priorityInput = document.getElementById("today-detail-priority-input");
        var statusInput = document.getElementById("today-detail-status-input");
        var dueDateInput = document.getElementById("today-detail-due-date-input");
        var projectInput = document.getElementById("today-detail-project-input");
        var tagsInput = document.getElementById("today-detail-tags-input");
        var descriptionInput = document.getElementById("today-detail-description-input");
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
            status.className = "today-detail-status today-detail-status-" + (
                trigger.dataset.status === "已完成" ? "done" : "todo"
            );
            priority.textContent = trigger.dataset.priority || "未设置";
            priority.className = "today-detail-priority today-detail-priority-" + (
                trigger.dataset.priorityClass || "low"
            );
            meta.textContent = trigger.dataset.meta || "暂无截止日期";
            project.textContent = trigger.dataset.project || "未归属项目";
            tag.textContent = trigger.dataset.tag || "未分类";
            description.textContent = trigger.dataset.description || "暂无描述";
            updated.textContent = trigger.dataset.updated || "暂无更新时间";
            editLink.href = trigger.dataset.editUrl || "#";
            form.action = trigger.dataset.updateUrl || "#";
            titleInput.value = trigger.dataset.title || "";
            priorityInput.value = trigger.dataset.priorityValue || "中";
            statusInput.value = trigger.dataset.status || "待办";
            dueDateInput.value = trigger.dataset.dueDate || "";
            projectInput.value = trigger.dataset.projectId || "";
            tagsInput.value = trigger.dataset.tags || "";
            descriptionInput.value = trigger.dataset.description === "暂无描述" ? "" : (trigger.dataset.description || "");

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

        document.addEventListener("click", function (event) {
            var trigger = event.target.closest("[data-today-detail], [data-task-detail]");
            if (!trigger || drawer.contains(trigger)) {
                return;
            }
            openDrawer(trigger);
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
