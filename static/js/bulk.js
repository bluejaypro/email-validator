// Bulk email validation
(function () {
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

        // Prefer file upload over textarea
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
            await validateBulk(emails);
        }
    });

    async function validateBulk(emails) {
        setLoading(btn, true);
        resultArea.innerHTML = "";

        try {
            const res = await fetch("/api/validate/bulk", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ emails }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Bulk validation failed");
            }

            const data = await res.json();
            resultArea.innerHTML = renderBulkResult(data);
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

            const res = await fetch("/api/validate/bulk/upload", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "File validation failed");
            }

            const data = await res.json();
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

        html += `<button class="export-btn" onclick="exportCSV()" aria-label="Export results as CSV">Export CSV</button>`;

        // Store data for export
        window._bulkResults = data;

        return html;
    }

    function renderStat(label, count, cls) {
        return `<div class="summary-stat ${cls}">
            <span class="count">${count}</span>
            <span class="label">${label}</span>
        </div>`;
    }

    function renderBulkItem(result) {
        let html = `<div class="bulk-item">`;
        html += `<button class="bulk-item-header" aria-expanded="false">`;
        html += `<span class="bulk-item-email">${escapeHtml(result.email)}</span>`;
        html += `<span class="bulk-item-verdict ${result.verdict}">${result.verdict}</span>`;
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

// CSV export (global so inline onclick works)
function exportCSV() {
    const data = window._bulkResults;
    if (!data) return;

    let csv = "Email,Verdict,Score,Details\n";
    for (const r of data.results) {
        const details = r.checks.map((c) => `${c.label}: ${c.message}`).join("; ");
        csv += `"${r.email}","${r.verdict}",${r.score},"${details}"\n`;
    }

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "email-validation-results.csv";
    a.click();
    URL.revokeObjectURL(url);
}
