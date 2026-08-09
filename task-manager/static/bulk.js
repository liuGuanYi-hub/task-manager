(function () {
    "use strict";

    var form = document.querySelector("[data-bulk-form]");
    if (!form) {
        return;
    }

    var selectAll = form.querySelector("[data-bulk-select-all]");
    var count = form.querySelector("[data-bulk-count]");
    var feedback = form.querySelector("[data-bulk-feedback]");
    var taskCheckboxes = Array.prototype.slice.call(document.querySelectorAll("[data-bulk-task]"));
    var submitButtons = Array.prototype.slice.call(form.querySelectorAll("[data-bulk-submit]"));

    function selectedTasks() {
        return taskCheckboxes.filter(function (checkbox) {
            return checkbox.checked;
        });
    }

    function render() {
        var selected = selectedTasks();
        var selectedCount = selected.length;
        if (count) {
            count.textContent = selectedCount ? "已选择 " + selectedCount + " 个任务" : "未选择任务";
        }
        if (selectAll) {
            selectAll.checked = taskCheckboxes.length > 0 && selectedCount === taskCheckboxes.length;
            selectAll.indeterminate = selectedCount > 0 && selectedCount < taskCheckboxes.length;
            selectAll.disabled = taskCheckboxes.length === 0;
        }
        submitButtons.forEach(function (button) {
            button.disabled = selectedCount === 0;
        });
    }

    function showFeedback(message) {
        if (feedback) {
            feedback.textContent = message;
        }
    }

    if (selectAll) {
        selectAll.addEventListener("change", function () {
            taskCheckboxes.forEach(function (checkbox) {
                checkbox.checked = selectAll.checked;
            });
            showFeedback("");
            render();
        });
    }

    taskCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
            showFeedback("");
            render();
        });
    });

    form.addEventListener("submit", function (event) {
        var selectedCount = selectedTasks().length;
        if (!selectedCount) {
            event.preventDefault();
            showFeedback("请先选择至少一个任务。");
            render();
            return;
        }
        if (event.submitter && event.submitter.value === "archive" && !window.confirm("确定归档选中的 " + selectedCount + " 个任务？")) {
            event.preventDefault();
        }
    });

    render();
})();
