(function () {
    "use strict";

    function initBoardInteractions() {
        const root = document.querySelector("[data-board-root]");
        if (!root) return;

        const columns = Array.from(root.querySelectorAll("[data-board-column]"));
        const dropzones = Array.from(root.querySelectorAll("[data-board-dropzone]"));
        const cards = Array.from(root.querySelectorAll("[data-board-card]"));
        const liveRegion = root.querySelector("[data-board-live]");
        let draggedCard = null;
        let keyboardOrigin = null;
        let suppressDragEndAnnouncement = false;
        let toastTimer = null;

        function announce(message) {
            if (liveRegion) liveRegion.textContent = message;
        }

        function showToast(message) {
            let toast = document.querySelector("[data-board-toast]");
            if (!toast) {
                toast = document.createElement("div");
                toast.className = "board-toast";
                toast.dataset.boardToast = "true";
                toast.setAttribute("role", "status");
                document.body.appendChild(toast);
            }
            toast.textContent = message;
            toast.classList.add("is-visible");
            window.clearTimeout(toastTimer);
            toastTimer = window.setTimeout(function () {
                toast.classList.remove("is-visible");
            }, 2600);
        }

        function getColumnLabel(column) {
            const title = column && column.querySelector(".board-column-title");
            return title ? title.textContent.trim() : "目标列";
        }

        function syncColumn(column) {
            if (!column) return;
            const dropzone = column.querySelector("[data-board-dropzone]");
            const cardsInColumn = dropzone ? dropzone.querySelectorAll("[data-board-card]") : [];
            const count = column.querySelector("[data-board-count]");
            const empty = column.querySelector("[data-board-empty]");
            if (count) count.textContent = String(cardsInColumn.length);
            if (empty) empty.hidden = cardsInColumn.length > 0;
        }

        function syncColumns() {
            columns.forEach(syncColumn);
        }

        function clearDropTargets() {
            dropzones.forEach(function (dropzone) {
                dropzone.classList.remove("is-drop-target");
            });
        }

        function persistCardMove(card, sourceColumn, targetColumn) {
            const statusUrl = card.dataset.boardStatusUrl;
            if (!statusUrl) {
                announce("任务已移动，但当前卡片没有可用的保存地址");
                showToast("移动未保存");
                return;
            }

            const saveToken = String(Date.now()) + "-" + Math.random().toString(16).slice(2);
            card.dataset.boardSaveToken = saveToken;
            const body = new URLSearchParams();
            body.set("status", targetColumn.dataset.boardColumn || "");

            fetch(statusUrl, {
                method: "POST",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                },
                body: body.toString(),
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("看板状态保存失败");
                    return response.json();
                })
                .then(function () {
                    if (card.dataset.boardSaveToken !== saveToken) return;
                    announce("任务已保存到" + getColumnLabel(targetColumn) + "列");
                    showToast("已保存到" + getColumnLabel(targetColumn));
                })
                .catch(function () {
                    if (card.dataset.boardSaveToken !== saveToken) return;
                    const sourceDropzone = sourceColumn && sourceColumn.querySelector("[data-board-dropzone]");
                    if (sourceDropzone) sourceDropzone.appendChild(card);
                    syncColumn(sourceColumn);
                    syncColumn(targetColumn);
                    card.classList.add("is-save-error");
                    window.setTimeout(function () {
                        card.classList.remove("is-save-error");
                    }, 700);
                    announce("保存失败，任务已恢复到原状态");
                    showToast("保存失败，已恢复原状态");
                });
        }

        function moveCard(card, targetColumn, announceMove) {
            if (!card || !targetColumn) return false;
            const sourceColumn = card.closest("[data-board-column]");
            const targetDropzone = targetColumn.querySelector("[data-board-dropzone]");
            if (!targetDropzone) return false;

            if (sourceColumn === targetColumn) {
                if (announceMove) announce("任务已经在" + getColumnLabel(targetColumn) + "列");
                return false;
            }

            targetDropzone.appendChild(card);
            card.classList.add("is-just-moved");
            window.setTimeout(function () {
                card.classList.remove("is-just-moved");
            }, 500);
            syncColumn(sourceColumn);
            syncColumn(targetColumn);

            if (announceMove) {
                const label = getColumnLabel(targetColumn);
                announce("正在保存到" + label + "列");
                showToast("正在保存到" + label);
            }
            persistCardMove(card, sourceColumn, targetColumn);
            return true;
        }

        function resetDragState() {
            if (draggedCard) draggedCard.classList.remove("is-dragging");
            root.classList.remove("is-dragging-board");
            clearDropTargets();
            draggedCard = null;
        }

        function handleDragStart(event) {
            const card = event.currentTarget;
            if (event.target.closest("a, button, select, input, textarea")) {
                event.preventDefault();
                return;
            }
            draggedCard = card;
            suppressDragEndAnnouncement = false;
            card.classList.add("is-dragging");
            root.classList.add("is-dragging-board");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", card.dataset.taskId || "");
            announce("已抓取任务，请拖到目标状态列");
        }

        function handleDragOver(event) {
            if (!draggedCard) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            event.currentTarget.classList.add("is-drop-target");
        }

        function handleDragLeave(event) {
            const dropzone = event.currentTarget;
            if (event.relatedTarget && dropzone.contains(event.relatedTarget)) return;
            dropzone.classList.remove("is-drop-target");
        }

        function handleDrop(event) {
            if (!draggedCard) return;
            event.preventDefault();
            const targetColumn = event.currentTarget.closest("[data-board-column]");
            moveCard(draggedCard, targetColumn, true);
            suppressDragEndAnnouncement = true;
            resetDragState();
        }

        function handleDragEnd() {
            if (!suppressDragEndAnnouncement) announce("已取消拖拽");
            suppressDragEndAnnouncement = false;
            resetDragState();
        }

        function handleToggle(event) {
            const button = event.currentTarget;
            const column = button.closest("[data-board-column]");
            const cardsPanel = column && column.querySelector("[data-board-dropzone]");
            if (!cardsPanel) return;
            const willExpand = cardsPanel.hidden;
            cardsPanel.hidden = !willExpand;
            button.setAttribute("aria-expanded", String(willExpand));
            const icon = button.querySelector(".board-column-toggle-icon");
            if (icon) icon.textContent = willExpand ? "⌃" : "⌄";
            column.classList.toggle("is-collapsed", !willExpand);
            announce((willExpand ? "已展开" : "已收起") + getColumnLabel(column) + "列");
        }

        function releaseKeyboardCard(card, message) {
            card.classList.remove("board-keyboard-grabbed");
            card.setAttribute("aria-grabbed", "false");
            keyboardOrigin = null;
            if (message) {
                announce(message);
                showToast("操作完成");
            }
        }

        function handleCardKeydown(event) {
            const card = event.currentTarget;
            const isGrabbed = card.classList.contains("board-keyboard-grabbed");
            if (event.key === " " || event.key === "Enter") {
                event.preventDefault();
                if (isGrabbed) {
                    releaseKeyboardCard(card, "已放下任务");
                } else {
                    keyboardOrigin = card.closest("[data-board-column]");
                    card.classList.add("board-keyboard-grabbed");
                    card.setAttribute("aria-grabbed", "true");
                    announce("已抓取任务，请使用左右方向键移动，按 Enter 放下，按 Escape 取消");
                }
                return;
            }
            if (!isGrabbed) return;

            if (event.key === "Escape") {
                event.preventDefault();
                if (keyboardOrigin) moveCard(card, keyboardOrigin, false);
                releaseKeyboardCard(card, "已取消移动");
                return;
            }

            if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
            event.preventDefault();
            const currentColumn = card.closest("[data-board-column]");
            const currentIndex = columns.indexOf(currentColumn);
            const nextIndex = event.key === "ArrowLeft" ? currentIndex - 1 : currentIndex + 1;
            const targetColumn = columns[nextIndex];
            if (!targetColumn) {
                announce("已经到达看板边界");
                return;
            }
            moveCard(card, targetColumn, true);
            card.focus();
        }

        cards.forEach(function (card) {
            card.setAttribute("aria-grabbed", "false");
            card.addEventListener("dragstart", handleDragStart);
            card.addEventListener("dragend", handleDragEnd);
            card.addEventListener("keydown", handleCardKeydown);
        });
        dropzones.forEach(function (dropzone) {
            dropzone.addEventListener("dragover", handleDragOver);
            dropzone.addEventListener("dragleave", handleDragLeave);
            dropzone.addEventListener("drop", handleDrop);
        });
        root.querySelectorAll("[data-board-toggle]").forEach(function (button) {
            button.addEventListener("click", handleToggle);
        });
        syncColumns();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initBoardInteractions);
    } else {
        initBoardInteractions();
    }
})();
