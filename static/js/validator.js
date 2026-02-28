// Request timeout (30 seconds)
const REQUEST_TIMEOUT_MS = 30000;

// Single email validation
(function () {
    const form = document.getElementById("single-form");
    const input = document.getElementById("email-input");
    const btn = document.getElementById("validate-btn");
    const resultArea = document.getElementById("single-result");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = input.value.trim();
        if (!email) {
            input.focus();
            return;
        }

        setLoading(btn, true);
        resultArea.innerHTML = "";

        try {
            const data = await fetchWithTimeout("/api/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            resultArea.innerHTML = renderResultCard(data);
            bindSuggestion(resultArea, input);
        } catch (err) {
            resultArea.innerHTML = renderError(err.message);
        } finally {
            setLoading(btn, false);
        }
    });

    function bindSuggestion(container, emailInput) {
        const link = container.querySelector(".suggestion-link");
        if (link) {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                emailInput.value = link.dataset.email;
                form.dispatchEvent(new Event("submit"));
            });
        }
    }
})();

// Shared utility: fetch with timeout and error handling
async function fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs || REQUEST_TIMEOUT_MS);

    try {
        const res = await fetch(url, { ...options, signal: controller.signal });

        if (res.status === 429) {
            throw new Error("Rate limit exceeded. Please wait a moment and try again.");
        }

        if (!res.ok) {
            let detail = `Server error (${res.status})`;
            try {
                const err = await res.json();
                detail = err.detail || detail;
            } catch {
                // Response wasn't JSON
            }
            throw new Error(detail);
        }

        return await res.json();
    } catch (err) {
        if (err.name === "AbortError") {
            throw new Error("Request timed out. The server may be busy.");
        }
        throw err;
    } finally {
        clearTimeout(timeout);
    }
}

// Shared rendering functions
function setLoading(btn, loading) {
    btn.disabled = loading;
    btn.classList.toggle("loading", loading);
}

function renderResultCard(data) {
    const verdictLabels = {
        valid: "Valid Email",
        invalid: "Invalid Email",
        warning: "Warning",
        unknown: "Unknown",
    };

    let html = `<div class="result-card ${escapeAttr(data.verdict)}">`;
    html += `<div class="verdict">`;
    html += `<span class="verdict-label ${escapeAttr(data.verdict)}">${escapeHtml(verdictLabels[data.verdict] || "Unknown")}</span>`;
    html += `<span class="score-badge ${escapeAttr(data.verdict)}">Score: ${Math.round(data.score * 100)}%</span>`;
    html += `</div>`;

    if (data.suggestion) {
        html += `<div class="suggestion">`;
        html += `<span>Did you mean </span>`;
        html += `<a class="suggestion-link" href="#" data-email="${escapeAttr(data.suggestion)}">${escapeHtml(data.suggestion)}</a>?`;
        html += `</div>`;
    }

    html += `<ul class="checks-list">`;
    for (const check of data.checks) {
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
    html += `</ul></div>`;

    return html;
}

function renderError(message) {
    return `<div class="result-card invalid">
        <div class="verdict">
            <span class="verdict-label invalid">Error</span>
        </div>
        <p style="color: var(--text-muted); font-size: 14px;">${escapeHtml(message)}</p>
    </div>`;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
}

function escapeAttr(str) {
    return String(str).replace(/[&"'<>]/g, (c) => ({
        "&": "&amp;", '"': "&quot;", "'": "&#39;", "<": "&lt;", ">": "&gt;",
    })[c]);
}
