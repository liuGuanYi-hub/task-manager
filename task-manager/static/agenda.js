(function () {
    "use strict";

    function initAgendaInteractions() {
        var root = document.querySelector("[data-agenda-root]");
        if (!root) return;

        var dropzones = Array.prototype.slice.call(root.querySelectorAll("[data-agenda-dropzone]"));
        var feedback = root.querySelector("[data-agenda-feedback]");
        var draggedCard = null;
        var sourceZone = null;
        var sourceDate = "";

        function announce(message) {
            if (feedback) feedback.textContent = message;
        }

        function syncZone(zone) {
            if (!zone) return;
            var cards = zone.querySelectorAll("[data-agenda-task]");
            var empty = zone.querySelector("[data-agenda-empty]");
            if (empty) empty.hidden = cards.length > 0;
            var section = zone.closest(".agenda-section");
            var count = section && section.querySelector("[data-agenda-count]");
            if (count) count.textContent = cards.length + " 项任务";
        }

        function clearDragState() {
            if (draggedCard) draggedCard.classList.remove("is-agenda-dragging");
            dropzones.forEach(function (zone) { zone.classList.remove("is-agenda-drop-target"); });
            draggedCard = null;
            sourceZone = null;
            sourceDate = "";
        }

        function handleDragStart(event) {
            var card = event.currentTarget;
            if (card.dataset.agendaDate === "" || !card.dataset.agendaRescheduleUrl) {
                event.preventDefault();
                return;
            }
            draggedCard = card;
            sourceZone = card.closest("[data-agenda-dropzone]");
            sourceDate = card.dataset.agendaDate || "";
            card.classList.add("is-agenda-dragging");
            if (event.dataTransfer) {
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", card.dataset.agendaTaskId || card.dataset.taskId || "");
            }
            announce("正在移动任务，请放到目标日期");
        }

        function handleDragOver(event) {
            if (!draggedCard) return;
            var zone = event.currentTarget;
            var targetDate = zone.dataset.agendaDropDate || "";
            if (!targetDate || targetDate === sourceDate) return;
            event.preventDefault();
            if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
            zone.classList.add("is-agenda-drop-target");
        }

        function handleDragLeave(event) {
            var zone = event.currentTarget;
            if (event.relatedTarget && zone.contains(event.relatedTarget)) return;
            zone.classList.remove("is-agenda-drop-target");
        }

        function handleDrop(event) {
            if (!draggedCard) return;
            event.preventDefault();
            var targetZone = event.currentTarget;
            var targetDate = targetZone.dataset.agendaDropDate || "";
            if (!targetDate || targetDate === sourceDate) {
                clearDragState();
                return;
            }

            var card = draggedCard;
            var originalZone = sourceZone;
            var originalDate = sourceDate;
            var actionUrl = card.dataset.agendaRescheduleUrl;
            targetZone.appendChild(card);
            card.dataset.agendaDate = targetDate;
            syncZone(originalZone);
            syncZone(targetZone);
            announce("正在保存到 " + targetDate + "…");
            clearDragState();

            var body = new URLSearchParams();
            body.set("date", targetDate);
            fetch(actionUrl, {
                method: "POST",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
                },
                body: body.toString()
            })
                .then(function (response) {
                    return response.json().then(function (payload) {
                        if (!response.ok) {
                            throw new Error(payload.error && payload.error.message ? payload.error.message : "任务改期失败");
                        }
                        return payload;
                    });
                })
                .then(function () {
                    announce("已改期到 " + targetDate);
                    window.setTimeout(function () { window.location.reload(); }, 500);
                })
                .catch(function (error) {
                    if (originalZone) originalZone.appendChild(card);
                    card.dataset.agendaDate = originalDate;
                    syncZone(originalZone);
                    syncZone(targetZone);
                    card.classList.add("is-agenda-save-error");
                    window.setTimeout(function () { card.classList.remove("is-agenda-save-error"); }, 700);
                    announce(error.message || "保存失败，任务已恢复原日期");
                });
        }

        root.querySelectorAll("[data-agenda-task]").forEach(function (card) {
            card.dataset.agendaTaskId = card.dataset.taskId || "";
            card.addEventListener("dragstart", handleDragStart);
            card.addEventListener("dragend", clearDragState);
        });
        dropzones.forEach(function (zone) {
            zone.addEventListener("dragover", handleDragOver);
            zone.addEventListener("dragleave", handleDragLeave);
            zone.addEventListener("drop", handleDrop);
            syncZone(zone);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAgendaInteractions);
    } else {
        initAgendaInteractions();
    }
})();
