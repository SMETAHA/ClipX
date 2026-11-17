(() => {
    const BUSY_CLASS = "live-busy";

    function sameOriginUrl(rawUrl) {
        try {
            return new URL(rawUrl, window.location.href);
        } catch (_) {
            return null;
        }
    }

    function shouldSkipLink(link, event) {
        if (!link) return true;
        if (event.defaultPrevented) return true;
        if (event.button !== 0) return true;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return true;
        if (link.target && link.target !== "_self") return true;
        if (link.hasAttribute("download")) return true;
        if (link.dataset.noAjax === "true" || link.closest("[data-no-ajax='true']")) return true;

        const url = sameOriginUrl(link.href);
        if (!url || url.origin !== window.location.origin) return true;

        // These routes intentionally return binary/downloadable content.
        if (url.pathname.startsWith("/raw/")) return true;
        if (url.pathname.startsWith("/download/")) return true;
        if (url.pathname === "/export") return true;
        return false;
    }

    function shouldSkipForm(form, submitter) {
        if (!form) return true;
        if (form.dataset.noAjax === "true" || submitter?.dataset?.noAjax === "true") return true;

        const actionUrl = sameOriginUrl(submitter?.getAttribute("formaction") || form.action || window.location.href);
        if (!actionUrl || actionUrl.origin !== window.location.origin) return true;

        const actionValue = form.querySelector("select[name='action']")?.value;
        if (actionUrl.pathname === "/bulk" && actionValue === "export") return true;
        if (actionUrl.pathname === "/export") return true;
        return false;
    }

    function setBusy(isBusy) {
        document.documentElement.classList.toggle(BUSY_CLASS, Boolean(isBusy));
    }

    function toast(text, type = "ok") {
        let box = document.getElementById("live-toast");
        if (!box) {
            box = document.createElement("div");
            box.id = "live-toast";
            box.className = "live-toast";
            document.body.appendChild(box);
        }
        box.textContent = text;
        box.dataset.type = type;
        box.classList.add("show");
        clearTimeout(box._timer);
        box._timer = setTimeout(() => box.classList.remove("show"), 1800);
    }

    function replaceMainFromHtml(html, url, pushHistory = true) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const newMain = doc.querySelector("[data-live-main]");
        const oldMain = document.querySelector("[data-live-main]");

        if (!newMain || !oldMain) {
            window.location.href = url || window.location.href;
            return;
        }

        oldMain.replaceWith(document.importNode(newMain, true));
        document.title = doc.title || document.title;

        if (pushHistory && url) {
            const current = window.location.pathname + window.location.search + window.location.hash;
            const next = new URL(url, window.location.origin);
            const nextPath = next.pathname + next.search + next.hash;
            if (current !== nextPath) {
                history.pushState({clipxLive: true}, "", nextPath);
            }
        }

        initPageBits();
    }

    async function fetchHtml(url, options = {}, pushHistory = true) {
        setBusy(true);
        try {
            const resp = await fetch(url, {
                credentials: "same-origin",
                redirect: "follow",
                ...options,
                headers: {
                    "X-ClipX-Live": "1",
                    ...(options.headers || {}),
                },
            });

            const contentType = resp.headers.get("content-type") || "";
            if (!resp.ok) {
                toast(`Ошибка ${resp.status}`, "bad");
                return;
            }
            if (!contentType.includes("text/html")) {
                // Most likely a file download/export. Fall back to normal navigation.
                window.location.href = typeof url === "string" ? url : resp.url;
                return;
            }

            const html = await resp.text();
            replaceMainFromHtml(html, resp.url, pushHistory);
        } catch (err) {
            console.error(err);
            toast("Сеть/сервер не ответил", "bad");
        } finally {
            setBusy(false);
        }
    }

    function formDataWithSubmitter(form, submitter) {
        try {
            return new FormData(form, submitter || undefined);
        } catch (_) {
            const data = new FormData(form);
            if (submitter?.name) data.append(submitter.name, submitter.value || "");
            return data;
        }
    }

    async function ajaxSubmit(form, submitter) {
        if (shouldSkipForm(form, submitter)) return false;

        const method = (submitter?.getAttribute("formmethod") || form.method || "get").toUpperCase();
        const action = submitter?.getAttribute("formaction") || form.action || window.location.href;
        const url = sameOriginUrl(action);
        if (!url) return false;

        if (method === "GET") {
            const data = new FormData(form);
            const params = new URLSearchParams();
            for (const [key, value] of data.entries()) {
                if (value instanceof File) continue;
                if (String(value).length) params.append(key, String(value));
            }
            url.search = params.toString();
            await fetchHtml(url.toString(), {method: "GET"}, true);
            return true;
        }

        const data = formDataWithSubmitter(form, submitter);
        await fetchHtml(url.toString(), {method, body: data}, false);
        return true;
    }

    async function entryToFiles(entry, path = "") {
        if (!entry) return [];
        if (entry.isFile) {
            return await new Promise((resolve) => {
                entry.file(
                    (file) => resolve([{file, path: path + file.name}]),
                    () => resolve([]),
                );
            });
        }
        if (entry.isDirectory) {
            const reader = entry.createReader();
            const entries = await new Promise((resolve) => reader.readEntries(resolve));
            const nested = await Promise.all(entries.map((e) => entryToFiles(e, path + entry.name + "/")));
            return nested.flat();
        }
        return [];
    }

    async function dataTransferToFiles(dataTransfer) {
        const items = Array.from(dataTransfer.items || []);
        const hasEntries = items.length && typeof items[0].webkitGetAsEntry === "function";
        if (hasEntries) {
            const groups = await Promise.all(items.map((item) => entryToFiles(item.webkitGetAsEntry())));
            return groups.flat();
        }
        return Array.from(dataTransfer.files || []).map((file) => ({file, path: file.webkitRelativePath || file.name}));
    }

    function activeUploadConfig() {
        const simpleForm = document.getElementById("simple-form");
        if (simpleForm) {
            return {
                url: simpleForm.action,
                next: simpleForm.querySelector("input[name='next']")?.value || "/simple",
            };
        }

        const uploadForm = document.getElementById("upload-form");
        if (uploadForm) {
            return {
                url: uploadForm.action,
                next: uploadForm.querySelector("input[name='next']")?.value || "/",
            };
        }

        return {url: "/quick-add", next: window.location.pathname + window.location.search};
    }

    async function uploadFilePairs(filePairs) {
        if (!filePairs.length) return;
        const cfg = activeUploadConfig();
        const formData = new FormData();
        formData.append("next", cfg.next);
        for (const pair of filePairs) {
            if (pair?.file) formData.append("file", pair.file, pair.path || pair.file.name || `paste-${Date.now()}`);
        }
        await fetchHtml(cfg.url, {method: "POST", body: formData}, false);
    }

    function bulkCheckedCount() {
        return document.querySelectorAll("#bulk-form input[name='item_ids']:checked").length;
    }

    function updateBulkState() {
        const form = document.getElementById("bulk-form");
        if (!form) return;

        const checkboxes = Array.from(form.querySelectorAll("input[name='item_ids']"));
        const checked = checkboxes.filter((checkbox) => checkbox.checked).length;
        const count = document.getElementById("bulk-count");
        const apply = document.getElementById("bulk-apply");
        const selectAll = document.getElementById("select-all");

        if (count) count.textContent = `Выбрано: ${checked}`;
        if (apply) apply.disabled = checked === 0;
        if (selectAll) {
            selectAll.checked = checkboxes.length > 0 && checked === checkboxes.length;
            selectAll.indeterminate = checked > 0 && checked < checkboxes.length;
        }
    }

    function confirmBulk(form) {
        const action = form.querySelector("select[name='action']")?.value;
        const checked = bulkCheckedCount();
        if (!checked) {
            alert("Ничего не выбрано.");
            updateBulkState();
            return false;
        }
        if (action === "delete") return confirm(`Удалить выбранные записи: ${checked}?`);
        return true;
    }

    async function copyText(text, button) {
        try {
            await navigator.clipboard.writeText(text || "");
            if (button) {
                const old = button.textContent;
                button.textContent = "Copied";
                setTimeout(() => button.textContent = old, 900);
            }
        } catch (_) {
            alert("Не удалось скопировать. Браузер не дал доступ к clipboard.");
        }
    }

    window.copyTextFromButton = async (button) => copyText(button?.dataset?.copyText || "", button);
    window.copyFromId = async (button) => {
        const el = document.getElementById(button?.dataset?.copyTarget || "");
        await copyText(el?.textContent || "", button);
    };
    window.copyFromPre = async () => {
        const el = document.getElementById("copy-source");
        await copyText(el?.textContent || "");
    };
    window.confirmBulk = confirmBulk;

    function showChosenFiles() {
        const files = [
            ...Array.from(document.getElementById("simple-file-input")?.files || []),
            ...Array.from(document.getElementById("simple-folder-input")?.files || []),
            ...Array.from(document.getElementById("file-input")?.files || []),
            ...Array.from(document.getElementById("folder-input")?.files || []),
        ];
        const box = document.getElementById("chosen-files") || document.getElementById("chosen-upload-files");
        if (!box) return;
        box.textContent = files.length ? `Выбрано файлов: ${files.length}` : "";
    }

    function initPageBits() {
        showChosenFiles();
        updateBulkState();
    }

    document.addEventListener("click", async (event) => {
        const link = event.target.closest?.("a[href]");
        if (!link || shouldSkipLink(link, event)) return;
        event.preventDefault();
        await fetchHtml(link.href, {method: "GET"}, true);
    });

    document.addEventListener("submit", async (event) => {
        const form = event.target;
        const submitter = event.submitter;
        if (!(form instanceof HTMLFormElement)) return;

        const actionUrl = sameOriginUrl(submitter?.getAttribute("formaction") || form.action || window.location.href);
        if (form.id === "bulk-form" && actionUrl?.pathname === "/bulk" && !confirmBulk(form)) {
            event.preventDefault();
            return;
        }

        if (shouldSkipForm(form, submitter)) return;

        event.preventDefault();
        await ajaxSubmit(form, submitter);
    });

    document.addEventListener("change", (event) => {
        const target = event.target;
        if (target?.id === "select-all") {
            document.querySelectorAll("input[name='item_ids']").forEach((checkbox) => {
                checkbox.checked = target.checked;
            });
            updateBulkState();
        }
        if (target?.name === "item_ids") {
            updateBulkState();
        }
        if (["simple-file-input", "simple-folder-input", "file-input", "folder-input"].includes(target?.id)) {
            showChosenFiles();
        }
    });

    ["dragenter", "dragover"].forEach((name) => {
        document.addEventListener(name, (event) => {
            event.preventDefault();
            const zone = document.getElementById("simple-drop") || document.getElementById("drop-zone");
            zone?.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach((name) => {
        document.addEventListener(name, () => {
            const zone = document.getElementById("simple-drop") || document.getElementById("drop-zone");
            zone?.classList.remove("drag-over");
        });
    });

    async function quickAddText(text) {
        const value = (text || "").trim();
        if (!value) return false;

        const formData = new FormData();
        formData.append("content", value);
        formData.append("next", window.location.pathname + window.location.search);
        await fetchHtml("/quick-add", {method: "POST", body: formData}, false);
        return true;
    }

    document.addEventListener("drop", async (event) => {
        event.preventDefault();
        const pairs = await dataTransferToFiles(event.dataTransfer);
        if (pairs.length) {
            await uploadFilePairs(pairs);
            return;
        }

        const droppedText = event.dataTransfer?.getData("text/plain") || event.dataTransfer?.getData("text/uri-list") || "";
        if (droppedText.trim()) {
            await quickAddText(droppedText);
        }
    });

    document.addEventListener("paste", async (event) => {
        const fileItems = Array.from(event.clipboardData?.items || []).filter((item) => item.kind === "file");
        if (fileItems.length) {
            const files = fileItems
                .map((item) => item.getAsFile())
                .filter(Boolean)
                .map((file) => ({file, path: file.name || `paste-${Date.now()}.png`}));
            await uploadFilePairs(files);
            return;
        }

        const tag = document.activeElement?.tagName || "";
        const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(tag);
        if (typing) return;
        const pastedText = event.clipboardData?.getData("text/plain") || "";
        if (pastedText.trim()) {
            event.preventDefault();
            await quickAddText(pastedText);
        }
    });

    document.addEventListener("keydown", (event) => {
        const tag = document.activeElement?.tagName || "";
        const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(tag);

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            document.getElementById("search-input")?.focus();
        }

        if (event.key === "/" && !typing) {
            event.preventDefault();
            document.getElementById("search-input")?.focus();
        }

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "u") {
            event.preventDefault();
            (document.getElementById("simple-file-input") || document.getElementById("file-input"))?.click();
        }

        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            const simpleForm = document.getElementById("simple-form");
            const textForm = document.getElementById("text-form");
            const targetForm = simpleForm || textForm;
            if (targetForm) {
                event.preventDefault();
                targetForm.requestSubmit();
            }
        }
    });

    window.addEventListener("popstate", () => {
        fetchHtml(window.location.href, {method: "GET"}, false);
    });

    document.addEventListener("DOMContentLoaded", initPageBits);
    initPageBits();
})();
