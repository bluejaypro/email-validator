// Bulk email validation with chunked processing for large lists
(function () {
    const CHUNK_SIZE = 5000;
    const BULK_TIMEOUT_MS = 120000; // 2 min per chunk

    const form = document.getElementById("bulk-form");
    const textarea = document.getElementById("bulk-input");
    const fileInput = document.getElementById("file-input");
    const fileName = document.getElementById("file-name");
    const btn = document.getElementById("bulk-validate-btn");
    const resultArea = document.getElementById("bulk-result");

    let selectedFile = null;

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            selectedFile = fileInput.files[0];
            fileName.textContent = selectedFile.name;
        }
    });

    // Allow Enter key on file upload label
    const fileLabel = document.querySelector(".file-upload");
    fileLabel.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInput.click();
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (selectedFile) {
            await validateFile(selectedFile);
        } else {
            const text = textarea.value.trim();
            if (!text) {
                textarea.focus();
                return;
            }
            const emails = text
                .split(/[\n,;]+/)
                .map((e) => e.trim())
                .filter((e) => e);
            await validateBulkChunked(emails);
        }
    });

    async function validateBulkChunked(emails) {
        setLoading(btn, true);
        resultArea.innerHTML = "";

        const chunks = [];
        for (let i = 0; i < emails.length; i += CHUNK_SIZE) {
            chunks.push(emails.slice(i, i + CHUNK_SIZE));
        }

        if (chunks.length > 1) {
            resultArea.innerHTML = renderProgress(0, chunks.length, emails.length);
        }

        const allResults = [];
        try {
            for (let i = 0; i < chunks.length; i++) {
                const data = await fetchWithTimeout(
                    "/api/validate/bulk",
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ emails: chunks[i] }),
                    },
                    BULK_TIMEOUT_MS
                );

                allResults.push(...data.results);

                if (chunks.length > 1) {
                    resultArea.innerHTML = renderProgress(i + 1, chunks.length, emails.length);
                }
            }

            const merged = mergeBulkResults(allResults);
            resultArea.innerHTML = renderBulkResult(merged);
            bindBulkInteractions();
        } catch (err) {
            resultArea.innerHTML = renderError(err.message);
        } finally {
            setLoading(btn, false);
        }
    }

    async function validateFile(file) {
        setLoading(btn, true);
        resultArea.innerHTML = "";

        try {
            const formData = new FormData();
            formData.append("file", file);

            const data = await fetchWithTimeout(
                "/api/validate/bulk/upload",
                { method: "POST", body: formData },
                BULK_TIMEOUT_MS
            );

            resultArea.innerHTML = renderBulkResult(data);
            bindBulkInteractions();
        } catch (err) {
            resultArea.innerHTML = renderError(err.message);
        } finally {
            setLoading(btn, false);
            selectedFile = null;
            fileInput.value = "";
            fileName.textContent = "";
        }
    }

    function mergeBulkResults(results) {
        const valid = results.filter((r) => r.verdict === "valid").length;
        const invalid = results.filter((r) => r.verdict === "invalid").length;
        const warnings = results.filter((r) => r.verdict === "warning").length;
        const unknown = results.filter((r) => r.verdict === "unknown").length;
        return { total: results.length, valid, invalid, warnings, unknown, results };
    }

    function renderProgress(done, total, emailCount) {
        const pct = Math.round((done / total) * 100);
        return `<div class="result-card unknown">
            <div class="verdict">
                <span class="verdict-label unknown">Processing ${emailCount.toLocaleString()} emails...</span>
                <span class="score-badge unknown">Batch ${done}/${total}</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: ${pct}%"></div>
            </div>
            <p style="color: var(--text-muted); font-size: 13px; margin-top: 8px;">
                ${(done * CHUNK_SIZE > emailCount ? emailCount : done * CHUNK_SIZE).toLocaleString()} of ${emailCount.toLocaleString()} emails processed
            </p>
        </div>`;
    }

    function renderBulkResult(data) {
        let html = `<div class="bulk-summary">`;
        html += renderStat("Total", data.total, "total");
        html += renderStat("Valid", data.valid, "valid");
        html += renderStat("Invalid", data.invalid, "invalid");
        html += renderStat("Warnings", data.warnings + (data.unknown || 0), "warnings");
        html += `</div>`;

        html += `<div class="bulk-results-list">`;
        for (const result of data.results) {
            html += renderBulkItem(result);
        }
        html += `</div>`;

        html += `<button class="export-btn" id="export-csv-btn" aria-label="Export results as CSV">Export CSV</button>`;

        // Store data for export and bind click
        window._bulkResults = data;
        setTimeout(() => {
            const exportBtn = document.getElementById("export-csv-btn");
            if (exportBtn) exportBtn.addEventListener("click", exportCSV);
        }, 0);

        return html;
    }

    function renderStat(label, count, cls) {
        return `<div class="summary-stat ${cls}">
            <span class="count">${count.toLocaleString()}</span>
            <span class="label">${escapeHtml(label)}</span>
        </div>`;
    }

    function renderBulkItem(result) {
        let html = `<div class="bulk-item">`;
        html += `<button class="bulk-item-header" aria-expanded="false">`;
        html += `<span class="bulk-item-email">${escapeHtml(result.email)}</span>`;
        html += `<span class="bulk-item-verdict ${escapeAttr(result.verdict)}">${escapeHtml(result.verdict)}</span>`;
        html += `<span class="bulk-item-expand" aria-hidden="true">&#9660;</span>`;
        html += `</button>`;

        html += `<div class="bulk-item-details">`;
        html += `<ul class="checks-list">`;
        for (const check of result.checks) {
            const iconClass =
                check.passed === true ? "pass" : check.passed === false ? "fail" : "unknown";
            const icon =
                check.passed === true ? "\u2713" : check.passed === false ? "\u2717" : "\u2014";
            html += `<li class="check-item">`;
            html += `<span class="check-icon ${iconClass}">${icon}</span>`;
            html += `<span class="check-label">${escapeHtml(check.label)}</span>`;
            html += `<span class="check-message">${escapeHtml(check.message)}</span>`;
            html += `</li>`;
        }
        html += `</ul></div></div>`;

        return html;
    }

    function bindBulkInteractions() {
        const headers = resultArea.querySelectorAll(".bulk-item-header");
        headers.forEach((header) => {
            header.addEventListener("click", () => {
                const item = header.closest(".bulk-item");
                const isOpen = item.classList.toggle("open");
                header.setAttribute("aria-expanded", isOpen);
            });
        });
    }
})();

// CSV export with proper field escaping
function exportCSV() {
    const data = window._bulkResults;
    if (!data) return;

    const rows = [["Email", "Verdict", "Score", "Details"]];
    for (const r of data.results) {
        const details = r.checks.map((c) => `${c.label}: ${c.message}`).join("; ");
        rows.push([r.email, r.verdict, String(r.score), details]);
    }

    const csv = rows
        .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
        .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "email-validation-results.csv";
    a.click();
    URL.revokeObjectURL(url);
}
