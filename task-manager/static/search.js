(function () {
    "use strict";

    function initGlobalSearch() {
        const layer = document.querySelector("[data-search-layer]");
        if (!layer) return;

        const dialog = layer.querySelector(".search-dialog");
        const input = layer.querySelector("[data-search-input]");
        const resultsContainer = layer.querySelector("[data-search-results]");
        const emptyState = layer.querySelector("[data-search-empty]");
        const loadingState = layer.querySelector("[data-search-loading]");
        const status = layer.querySelector("[data-search-status]");
        const endpoint = layer.dataset.searchEndpoint;
        let lastTrigger = null;
        let closeTimer = null;
        let queryTimer = null;
        let requestId = 0;

        function openSearch(trigger) {
            lastTrigger = trigger || document.querySelector("[data-search-open]");
            window.clearTimeout(closeTimer);
            layer.hidden = false;
            document.body.classList.add("search-open");
            window.requestAnimationFrame(function () {
                layer.classList.add("is-open");
            });
            if (input) {
                input.value = "";
                filterResults("");
                window.setTimeout(function () {
                    input.focus();
                }, 30);
            } else if (dialog) {
                dialog.focus();
            }
        }

        function closeSearch() {
            layer.classList.remove("is-open");
            document.body.classList.remove("search-open");
            window.clearTimeout(closeTimer);
            closeTimer = window.setTimeout(function () {
                if (!layer.classList.contains("is-open")) layer.hidden = true;
            }, 180);
            if (lastTrigger && typeof lastTrigger.focus === "function") lastTrigger.focus();
        }

        function resultIconLabel(kind) {
            return kind === "project" ? "P" : kind === "tag" ? "#" : "T";
        }

        function createResultItem(result) {
            const item = document.createElement("a");
            item.className = "search-result";
            item.dataset.searchItem = "true";
            item.href = result.url || "#";

            const icon = document.createElement("span");
            icon.className = "search-result-icon search-result-icon-" + (result.accent || "blue");
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = result.icon || resultIconLabel(result.kind);

            const copy = document.createElement("span");
            copy.className = "search-result-copy";
            const title = document.createElement("strong");
            title.textContent = result.title || "未命名结果";
            const subtitle = document.createElement("small");
            subtitle.textContent = result.subtitle || "";
            copy.appendChild(title);
            copy.appendChild(subtitle);

            const shortcut = document.createElement("kbd");
            shortcut.textContent = resultIconLabel(result.kind);
            item.appendChild(icon);
            item.appendChild(copy);
            item.appendChild(shortcut);
            return item;
        }

        function renderResults(payload, query) {
            if (!resultsContainer) return;
            resultsContainer.innerHTML = "";
            const results = payload && Array.isArray(payload.data) ? payload.data : [];
            results.forEach(function (result) {
                resultsContainer.appendChild(createResultItem(result));
            });
            if (loadingState) loadingState.hidden = true;
            if (emptyState) {
                emptyState.textContent = query ? "没有匹配的任务、项目或标签。" : "当前还没有可搜索的任务或项目。";
                emptyState.hidden = results.length > 0;
            }
            if (status) status.textContent = query ? results.length + " 条结果" : "最近任务";
        }

        function loadResults(rawQuery) {
            const query = rawQuery.trim();
            const currentRequest = ++requestId;
            if (!endpoint) return;
            if (loadingState) loadingState.hidden = false;
            if (emptyState) emptyState.hidden = true;
            fetch(endpoint + "?q=" + encodeURIComponent(query), {
                headers: {"Accept": "application/json"},
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("搜索请求失败");
                    return response.json();
                })
                .then(function (payload) {
                    if (currentRequest !== requestId) return;
                    renderResults(payload, query);
                })
                .catch(function () {
                    if (currentRequest !== requestId) return;
                    if (loadingState) loadingState.hidden = true;
                    if (emptyState) {
                        emptyState.textContent = "搜索暂时不可用，请稍后重试。";
                        emptyState.hidden = false;
                    }
                    if (status) status.textContent = "搜索失败";
                });
        }

        function filterResults(rawQuery) {
            window.clearTimeout(queryTimer);
            queryTimer = window.setTimeout(function () {
                loadResults(rawQuery);
            }, 140);
        }

        function isTypingTarget(target) {
            if (!target) return false;
            const name = target.tagName ? target.tagName.toLowerCase() : "";
            return name === "input" || name === "textarea" || name === "select" || target.isContentEditable;
        }

        function runCommandShortcut(event) {
            if (layer.hidden || isTypingTarget(event.target)) return false;
            const key = event.key.toLowerCase();
            const command = layer.querySelector('[data-search-command="' + key + '"]');
            if (!command) return false;
            event.preventDefault();
            window.location.href = command.href;
            return true;
        }

        document.querySelectorAll("[data-search-open]").forEach(function (trigger) {
            trigger.addEventListener("click", function () {
                openSearch(trigger);
            });
        });
        layer.querySelectorAll("[data-search-close]").forEach(function (button) {
            button.addEventListener("click", closeSearch);
        });
        if (input) input.addEventListener("input", function () {
            filterResults(input.value);
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !layer.hidden) {
                event.preventDefault();
                closeSearch();
                return;
            }
            if (isTypingTarget(event.target)) return;
            if (runCommandShortcut(event)) return;
            if (event.key === "/" || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k")) {
                event.preventDefault();
                openSearch();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initGlobalSearch);
    } else {
        initGlobalSearch();
    }
})();
