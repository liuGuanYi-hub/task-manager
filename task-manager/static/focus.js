(function () {
    "use strict";

    var root = document.querySelector("[data-focus-timer]");
    if (!root) {
        return;
    }

    var storageKey = root.dataset.focusStorageKey || "task-manager:focus-timer:v1";
    var display = root.querySelector("[data-focus-display]");
    var stateLabel = root.querySelector("[data-focus-state]");
    var message = root.querySelector("[data-focus-message]");
    var progress = root.querySelector("[data-focus-progress]");
    var progressBar = root.querySelector(".today-timer-progress");
    var taskLabel = root.querySelector("[data-focus-task-label]");
    var clearTaskButton = root.querySelector("[data-focus-task-clear]");
    var taskSelectors = Array.prototype.slice.call(document.querySelectorAll("[data-focus-task-select]"));
    var startButton = root.querySelector("[data-focus-start]");
    var resetButton = root.querySelector("[data-focus-reset]");
    var presets = Array.prototype.slice.call(root.querySelectorAll("[data-focus-preset]"));
    var timerId = null;
    var state = createState(25);

    function createState(minutes) {
        var duration = Math.max(1, Number(minutes) || 25) * 60;
        return {
            durationSeconds: duration,
            remainingSeconds: duration,
            status: "idle",
            startedAt: null,
            focusTask: null
        };
    }

    function isValidState(value) {
        return value && ["idle", "running", "paused", "complete"].indexOf(value.status) !== -1
            && Number.isFinite(value.durationSeconds)
            && value.durationSeconds > 0
            && Number.isFinite(value.remainingSeconds)
            && value.remainingSeconds >= 0
            && value.remainingSeconds <= value.durationSeconds;
    }

    function loadState() {
        try {
            var saved = JSON.parse(window.localStorage.getItem(storageKey) || "null");
            if (isValidState(saved)) {
                state = saved;
                state.focusTask = normaliseFocusTask(saved.focusTask);
            }
        } catch (error) {
            state = createState(25);
        }
    }

    function normaliseFocusTask(value) {
        if (!value || value.id === undefined || value.id === null || !String(value.title || "").trim()) {
            return null;
        }
        return {
            id: String(value.id),
            title: String(value.title).trim()
        };
    }

    function saveState() {
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(state));
        } catch (error) {
            // 隐私模式或浏览器禁用存储时，计时仍可在当前页面继续。
        }
    }

    function remainingSeconds() {
        if (state.status !== "running" || !state.startedAt) {
            return state.remainingSeconds;
        }
        return Math.max(0, state.durationSeconds - Math.floor((Date.now() - state.startedAt) / 1000));
    }

    function formatTime(seconds) {
        var safeSeconds = Math.max(0, Math.floor(seconds));
        var minutes = String(Math.floor(safeSeconds / 60)).padStart(2, "0");
        var remainder = String(safeSeconds % 60).padStart(2, "0");
        return minutes + ":" + remainder;
    }

    function stateCopy() {
        return {
            idle: { label: "准备开始", message: "状态只保存在当前浏览器，刷新页面后会继续。" },
            running: { label: "专注中", message: "专注进行中，完成这一小段再切换任务。" },
            paused: { label: "已暂停", message: "计时已暂停，准备好后可以继续。" },
            complete: { label: "已完成", message: "本轮专注完成，休息一下再开始下一轮。" }
        }[state.status];
    }

    function render() {
        state.remainingSeconds = remainingSeconds();
        if (state.status === "running" && state.remainingSeconds === 0) {
            state.status = "complete";
            state.startedAt = null;
            saveState();
            stopTicker();
        }

        var copy = stateCopy();
        var ratio = state.durationSeconds ? state.remainingSeconds / state.durationSeconds : 0;
        display.textContent = formatTime(state.remainingSeconds);
        display.setAttribute("aria-label", "专注剩余 " + formatTime(state.remainingSeconds));
        stateLabel.textContent = copy.label;
        message.textContent = copy.message + (state.focusTask ? " 当前任务：" + state.focusTask.title : " 可先从 Today 任务卡片选择专注任务。");
        if (taskLabel) {
            var taskName = taskLabel.querySelector("strong");
            if (taskName) {
                taskName.textContent = state.focusTask ? state.focusTask.title : "未选择任务";
            }
            taskLabel.classList.toggle("has-task", Boolean(state.focusTask));
        }
        progress.style.width = ((1 - ratio) * 100) + "%";
        progressBar.setAttribute("aria-valuemax", String(state.durationSeconds));
        progressBar.setAttribute("aria-valuenow", String(state.remainingSeconds));
        startButton.textContent = state.status === "running" ? "暂停" : (state.status === "complete" ? "再来一轮" : "开始专注");
        resetButton.disabled = state.status === "idle" && state.remainingSeconds === state.durationSeconds;
        presets.forEach(function (preset) {
            var selected = Number(preset.dataset.minutes) * 60 === state.durationSeconds;
            preset.classList.toggle("is-selected", selected);
            preset.setAttribute("aria-pressed", selected ? "true" : "false");
            preset.disabled = state.status === "running";
        });
        taskSelectors.forEach(function (selector) {
            var selected = state.focusTask && String(selector.dataset.focusTaskId) === state.focusTask.id;
            selector.classList.toggle("is-selected", Boolean(selected));
            selector.textContent = selected ? "当前专注" : "专注";
            selector.setAttribute("aria-pressed", selected ? "true" : "false");
            selector.disabled = state.status === "running";
        });
        if (clearTaskButton) {
            clearTaskButton.disabled = !state.focusTask || state.status === "running";
        }
    }

    function startTicker() {
        stopTicker();
        timerId = window.setInterval(render, 1000);
    }

    function stopTicker() {
        if (timerId) {
            window.clearInterval(timerId);
            timerId = null;
        }
    }

    function startOrPause() {
        if (state.status === "running") {
            state.remainingSeconds = remainingSeconds();
            state.status = "paused";
            state.startedAt = null;
            stopTicker();
        } else {
            if (state.status === "complete") {
                state.remainingSeconds = state.durationSeconds;
            }
            state.status = "running";
            state.startedAt = Date.now() - (state.durationSeconds - state.remainingSeconds) * 1000;
            startTicker();
        }
        saveState();
        render();
    }

    function reset() {
        var selectedTask = state.focusTask;
        state = createState(state.durationSeconds / 60);
        state.focusTask = selectedTask;
        saveState();
        stopTicker();
        render();
    }

    presets.forEach(function (preset) {
        preset.addEventListener("click", function () {
            if (state.status === "running") {
                return;
            }
            var selectedTask = state.focusTask;
            state = createState(Number(preset.dataset.minutes));
            state.focusTask = selectedTask;
            saveState();
            render();
        });
    });
    taskSelectors.forEach(function (selector) {
        selector.addEventListener("click", function () {
            if (state.status === "running") {
                return;
            }
            state.focusTask = normaliseFocusTask({
                id: selector.dataset.focusTaskId,
                title: selector.dataset.focusTaskTitle
            });
            saveState();
            render();
        });
    });
    if (clearTaskButton) {
        clearTaskButton.addEventListener("click", function () {
            if (state.status === "running") {
                return;
            }
            state.focusTask = null;
            saveState();
            render();
        });
    }
    startButton.addEventListener("click", startOrPause);
    resetButton.addEventListener("click", reset);
    document.addEventListener("visibilitychange", render);
    window.addEventListener("focus", render);

    loadState();
    render();
    if (state.status === "running") {
        startTicker();
    }
})();
