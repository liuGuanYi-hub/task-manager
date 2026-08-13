(function () {
    "use strict";

    function initAgendaInteractions() {
        var root = document.querySelector("[data-agenda-root]");
        if (!root) return;

        var dropzones = Array.prototype.slice.call(root.querySelectorAll("[data-agenda-dropzone]"));
        var daySections = Array.prototype.slice.call(root.querySelectorAll("[data-agenda-day]"));
        var cards = Array.prototype.slice.call(root.querySelectorAll("[data-agenda-task]"));
        var feedback = root.querySelector("[data-agenda-feedback]");
        var draggedCard = null;
        var sourceZone = null;
        var sourceDate = "";
        var touchState = null;
        var keyboardState = null;
        var touchHoldTimer = null;

        function announce(message) {
            if (feedback) feedback.textContent = message;
        }

        function syncZone(zone) {
            if (!zone) return;
            var zoneCards = zone.querySelectorAll("[data-agenda-task]");
            var empty = zone.querySelector("[data-agenda-empty]");
            if (empty) empty.hidden = zoneCards.length > 0;
            var section = zone.closest(".agenda-section");
            var count = section && section.querySelector("[data-agenda-count]");
            if (count) count.textContent = zoneCards.length + " 项任务";
        }

        function clearDropHighlights() {
            dropzones.forEach(function (zone) {
                zone.classList.remove("is-agenda-drop-target");
                zone.classList.remove("is-agenda-touch-target");
            });
        }

        function clearDragState() {
            if (draggedCard) draggedCard.classList.remove("is-agenda-dragging");
            clearDropHighlights();
            draggedCard = null;
            sourceZone = null;
            sourceDate = "";
        }

        function setDragSource(card) {
            draggedCard = card;
            sourceZone = card.closest("[data-agenda-dropzone]");
            sourceDate = card.dataset.agendaDate || "";
            card.classList.add("is-agenda-dragging");
        }

        function findDropzoneAt(clientX, clientY) {
            var element = document.elementFromPoint(clientX, clientY);
            return element && element.closest ? element.closest("[data-agenda-dropzone]") : null;
        }

        function persistReschedule(card, targetZone, originalZone, originalDate) {
            var targetDate = targetZone && targetZone.dataset.agendaDropDate;
            var actionUrl = card && card.dataset.agendaRescheduleUrl;
            if (!card || !targetZone || !targetDate || !actionUrl || targetDate === originalDate) {
                return Promise.resolve(false);
            }

            targetZone.appendChild(card);
            card.dataset.agendaDate = targetDate;
            syncZone(originalZone);
            syncZone(targetZone);
            announce("正在保存到 " + targetDate + "…");

            var body = new URLSearchParams();
            body.set("date", targetDate);
            return fetch(actionUrl, {
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
                    return true;
                })
                .catch(function (error) {
                    if (originalZone) originalZone.appendChild(card);
                    card.dataset.agendaDate = originalDate;
                    syncZone(originalZone);
                    syncZone(targetZone);
                    card.classList.add("is-agenda-save-error");
                    window.setTimeout(function () { card.classList.remove("is-agenda-save-error"); }, 700);
                    announce(error.message || "保存失败，任务已恢复原日期");
                    return false;
                });
        }

        function handleDragStart(event) {
            var card = event.currentTarget;
            if (card.dataset.agendaDate === "" || !card.dataset.agendaRescheduleUrl) {
                event.preventDefault();
                return;
            }
            setDragSource(card);
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
            var card = draggedCard;
            var originalZone = sourceZone;
            var originalDate = sourceDate;
            var targetZone = event.currentTarget;
            var targetDate = targetZone.dataset.agendaDropDate || "";
            clearDragState();
            if (!targetDate || targetDate === originalDate) return;
            persistReschedule(card, targetZone, originalZone, originalDate);
        }

        function finishTouchDrag(clientX, clientY) {
            if (!touchState) return;
            var state = touchState;
            touchState = null;
            var targetZone = findDropzoneAt(clientX, clientY);
            if (state.card) state.card.classList.remove("is-agenda-touch-dragging");
            clearDropHighlights();
            if (!state.active || !targetZone || targetZone.dataset.agendaDropDate === state.sourceDate) {
                announce("已取消触控改期");
                return;
            }
            persistReschedule(state.card, targetZone, state.sourceZone, state.sourceDate);
        }

        function handleTouchStart(event) {
            var card = event.currentTarget;
            if (!card.dataset.agendaDate || !card.dataset.agendaRescheduleUrl || event.touches.length !== 1) return;
            var touch = event.touches[0];
            touchState = { card: card, sourceZone: card.closest("[data-agenda-dropzone]"), sourceDate: card.dataset.agendaDate, active: false };
            touchHoldTimer = window.setTimeout(function () {
                if (!touchState) return;
                touchState.active = true;
                card.classList.add("is-agenda-touch-dragging");
                announce("已抓取任务，请拖到目标日期后松手");
            }, 420);
        }

        function handleTouchMove(event) {
            if (!touchState || event.touches.length !== 1) return;
            var touch = event.touches[0];
            var moved = Math.abs(touch.clientX - touchState.startX) + Math.abs(touch.clientY - touchState.startY);
            if (!touchState.active && moved > 12) {
                window.clearTimeout(touchHoldTimer);
                touchState = null;
                return;
            }
            if (!touchState.active) return;
            var targetZone = findDropzoneAt(touch.clientX, touch.clientY);
            clearDropHighlights();
            if (targetZone && targetZone.dataset.agendaDropDate !== touchState.sourceDate) {
                event.preventDefault();
                targetZone.classList.add("is-agenda-touch-target");
            }
        }

        function handleTouchEnd(event) {
            window.clearTimeout(touchHoldTimer);
            if (!touchState) return;
            var touch = event.changedTouches[0];
            finishTouchDrag(touch.clientX, touch.clientY);
        }

        function moveKeyboardTarget(direction) {
            if (!keyboardState) return;
            var index = daySections.indexOf(keyboardState.section);
            var next = daySections[index + direction];
            if (!next) {
                announce(direction < 0 ? "已经到达时间线起点" : "已经到达时间线终点");
                return;
            }
            keyboardState.section.classList.remove("is-agenda-keyboard-target");
            keyboardState.section = next;
            next.classList.add("is-agenda-keyboard-target");
            next.scrollIntoView({ block: "nearest", behavior: "smooth" });
            announce("目标日期：" + next.dataset.agendaDay + "；按 Enter 保存，Esc 取消");
        }

        function handleKeyboard(event) {
            var card = event.currentTarget;
            if (!card.dataset.agendaDate || !card.dataset.agendaRescheduleUrl) return;
            if (!keyboardState && (event.key === "r" || event.key === "R")) {
                event.preventDefault();
                keyboardState = { card: card, sourceZone: card.closest("[data-agenda-dropzone]"), sourceDate: card.dataset.agendaDate, section: card.closest("[data-agenda-day]") };
                card.classList.add("is-agenda-keyboard-moving");
                if (keyboardState.section) keyboardState.section.classList.add("is-agenda-keyboard-target");
                announce("已进入键盘改期模式：左右键选择日期，Enter 保存，Esc 取消");
                return;
            }
            if (!keyboardState || keyboardState.card !== card) return;
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
                event.preventDefault();
                moveKeyboardTarget(event.key === "ArrowLeft" ? -1 : 1);
            } else if (event.key === "Enter") {
                event.preventDefault();
                var targetZone = keyboardState.section.querySelector("[data-agenda-dropzone]");
                var state = keyboardState;
                keyboardState = null;
                card.classList.remove("is-agenda-keyboard-moving");
                state.section.classList.remove("is-agenda-keyboard-target");
                if (targetZone && targetZone.dataset.agendaDropDate !== state.sourceDate) {
                    persistReschedule(card, targetZone, state.sourceZone, state.sourceDate);
                } else {
                    announce("任务仍在原日期");
                }
            } else if (event.key === "Escape") {
                event.preventDefault();
                keyboardState.section.classList.remove("is-agenda-keyboard-target");
                keyboardState = null;
                card.classList.remove("is-agenda-keyboard-moving");
                announce("已取消键盘改期");
            }
        }

        cards.forEach(function (card) {
            card.dataset.agendaTaskId = card.dataset.taskId || "";
            card.addEventListener("dragstart", handleDragStart);
            card.addEventListener("dragend", clearDragState);
            card.addEventListener("touchstart", function (event) {
                var touch = event.touches[0];
                if (touch) {
                    handleTouchStart({ currentTarget: card, touches: event.touches, preventDefault: event.preventDefault.bind(event) });
                    if (touchState) {
                        touchState.startX = touch.clientX;
                        touchState.startY = touch.clientY;
                    }
                }
            }, { passive: true });
            card.addEventListener("touchmove", handleTouchMove, { passive: false });
            card.addEventListener("touchend", handleTouchEnd, { passive: true });
            card.addEventListener("touchcancel", function () {
                window.clearTimeout(touchHoldTimer);
                if (touchState && touchState.card) touchState.card.classList.remove("is-agenda-touch-dragging");
                touchState = null;
                clearDropHighlights();
                announce("已取消触控改期");
            });
            card.addEventListener("keydown", handleKeyboard);
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
