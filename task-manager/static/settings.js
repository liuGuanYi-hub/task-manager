(function () {
    "use strict";

    var conflictSelect = document.querySelector("[data-conflict-select]");
    var conflictCard = document.querySelector("[data-conflict-strategy]");
    var conflictBadge = document.querySelector("[data-conflict-badge]");
    var conflictTitle = document.querySelector("[data-conflict-title]");
    var conflictDescription = document.querySelector("[data-conflict-description]");
    var conflictRisk = document.querySelector("[data-conflict-risk]");
    var conflictCopy = {
        remap: {
            badge: "推荐",
            title: "冲突时新建副本",
            description: "保留当前记录，并为导入内容分配新的 ID，适合先验证备份内容。",
            risk: "风险较低：不会覆盖当前任务。",
            tone: "safe"
        },
        skip: {
            badge: "保守",
            title: "冲突时跳过导入记录",
            description: "保留当前记录，只导入不存在的 ID，适合只补充新增内容。",
            risk: "影响较小：冲突记录不会进入当前数据。",
            tone: "neutral"
        },
        replace: {
            badge: "高风险",
            title: "冲突时覆盖同 ID 记录",
            description: "使用备份中的同 ID 内容替换当前记录，适合明确的恢复或回滚场景。",
            risk: "请先预览：同 ID 的当前内容可能被覆盖。",
            tone: "warning"
        }
    };

    function updateConflictGuide() {
        if (!conflictSelect || !conflictCard) {
            return;
        }
        var copy = conflictCopy[conflictSelect.value] || conflictCopy.remap;
        conflictCard.dataset.tone = copy.tone;
        conflictBadge.textContent = copy.badge;
        conflictTitle.textContent = copy.title;
        conflictDescription.textContent = copy.description;
        conflictRisk.textContent = copy.risk;
    }

    if (conflictSelect) {
        conflictSelect.addEventListener("change", updateConflictGuide);
        updateConflictGuide();
    }

    var drill = document.querySelector("[data-recovery-drill]");
    if (!drill) {
        return;
    }

    var STORAGE_KEY = "task-manager-recovery-drill-v1";
    var inputs = Array.prototype.slice.call(drill.querySelectorAll("[data-recovery-step]"));
    var progress = drill.querySelector("[data-recovery-progress]");
    var status = drill.querySelector("[data-recovery-status]");
    var saved = drill.querySelector("[data-recovery-saved]");
    var reset = drill.querySelector("[data-recovery-reset]");
    var state = {};

    function readState() {
        try {
            var stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
            return stored && typeof stored === "object" ? stored : {};
        } catch (error) {
            return {};
        }
    }

    function writeState() {
        var next = { steps: {}, updatedAt: new Date().toISOString() };
        inputs.forEach(function (input) {
            next.steps[input.dataset.recoveryStep] = input.checked;
        });
        state = next;
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch (error) {
            // 浏览器禁用本地存储时，仍保留当前页面的勾选状态。
        }
        updateDrillStatus();
    }

    function updateDrillStatus() {
        var completed = inputs.filter(function (input) { return input.checked; }).length;
        progress.textContent = completed + "/" + inputs.length;
        if (completed === inputs.length) {
            status.textContent = "已完成";
        } else if (completed > 0) {
            status.textContent = "进行中";
        } else {
            status.textContent = "尚未开始";
        }

        if (state.updatedAt && completed > 0) {
            var date = new Date(state.updatedAt);
            saved.textContent = "最近记录：" + (Number.isNaN(date.getTime()) ? "当前浏览器" : date.toLocaleString("zh-CN"));
        } else {
            saved.textContent = "仅保存在当前浏览器，不会写入任务数据。";
        }
    }

    state = readState();
    inputs.forEach(function (input) {
        input.checked = Boolean(state.steps && state.steps[input.dataset.recoveryStep]);
        input.addEventListener("change", writeState);
    });
    updateDrillStatus();

    if (reset) {
        reset.addEventListener("click", function () {
            inputs.forEach(function (input) { input.checked = false; });
            state = {};
            try {
                window.localStorage.removeItem(STORAGE_KEY);
            } catch (error) {
                // 浏览器禁用本地存储时，仅重置当前页面状态。
            }
            updateDrillStatus();
        });
    }
})();
