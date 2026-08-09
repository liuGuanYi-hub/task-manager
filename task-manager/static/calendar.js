(function () {
    "use strict";

    var root = document.querySelector("[data-calendar-root]");
    if (!root) {
        return;
    }

    var feedback = root.querySelector("[data-calendar-feedback]");
    var draggedTask = null;
    var busy = false;

    function setFeedback(message, isError) {
        if (!feedback) {
            return;
        }
        feedback.textContent = message;
        feedback.classList.toggle("is-error", Boolean(isError));
    }

    function clearDropTargets() {
        root.querySelectorAll("[data-calendar-drop-date].is-drag-over").forEach(function (target) {
            target.classList.remove("is-drag-over");
        });
    }

    function calendarTarget(event) {
        var target = event.target.closest("[data-calendar-drop-date]");
        return target && root.contains(target) ? target : null;
    }

    document.addEventListener("dragstart", function (event) {
        var source = event.target.closest("[data-calendar-task-id]");
        if (!source || !root.contains(source)) {
            return;
        }
        draggedTask = source;
        source.classList.add("is-dragging");
        if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", source.dataset.calendarTaskId || "");
        }
    });

    document.addEventListener("dragend", function () {
        if (draggedTask) {
            draggedTask.classList.remove("is-dragging");
        }
        draggedTask = null;
        clearDropTargets();
    });

    document.addEventListener("dragover", function (event) {
        var target = calendarTarget(event);
        if (!target || !draggedTask || busy) {
            return;
        }
        event.preventDefault();
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "move";
        }
        clearDropTargets();
        target.classList.add("is-drag-over");
    });

    document.addEventListener("dragleave", function (event) {
        var target = calendarTarget(event);
        if (target && (!event.relatedTarget || !target.contains(event.relatedTarget))) {
            target.classList.remove("is-drag-over");
        }
    });

    document.addEventListener("drop", function (event) {
        var target = calendarTarget(event);
        if (!target || !draggedTask || busy) {
            return;
        }
        event.preventDefault();
        clearDropTargets();

        var endpoint = draggedTask.dataset.calendarRescheduleUrl;
        var targetDate = target.dataset.calendarDropDate;
        if (!endpoint || !targetDate) {
            setFeedback("改期入口不可用，请使用任务详情编辑。", true);
            return;
        }

        busy = true;
        setFeedback("正在保存新的截止日期…", false);
        fetch(endpoint, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({date: targetDate})
        })
            .then(function (response) {
                return response.json().catch(function () {
                    return {};
                }).then(function (payload) {
                    if (!response.ok) {
                        throw new Error(payload.error && payload.error.message ? payload.error.message : "保存失败");
                    }
                    return payload;
                });
            })
            .then(function () {
                setFeedback("已改期至 " + targetDate + "，正在刷新日历。", false);
                window.setTimeout(function () {
                    window.location.reload();
                }, 220);
            })
            .catch(function (error) {
                busy = false;
                setFeedback(error.message || "改期失败，请稍后重试。", true);
            });
    });
})();
