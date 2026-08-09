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
            startedAt: null
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
            }
        } catch (error) {
            state = createState(25);
        }
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
        message.textContent = copy.message;
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
        state = createState(state.durationSeconds / 60);
        saveState();
        stopTicker();
        render();
    }

    presets.forEach(function (preset) {
        preset.addEventListener("click", function () {
            if (state.status === "running") {
                return;
            }
            state = createState(Number(preset.dataset.minutes));
            saveState();
            render();
        });
    });
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
