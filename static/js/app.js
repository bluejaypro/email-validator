// Tab switching
document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab");
    const panels = document.querySelectorAll(".panel");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.tab;

            tabs.forEach((t) => {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            tab.classList.add("active");
            tab.setAttribute("aria-selected", "true");

            panels.forEach((p) => {
                if (p.id === `panel-${target}`) {
                    p.classList.add("active");
                    p.removeAttribute("hidden");
                } else {
                    p.classList.remove("active");
                    p.setAttribute("hidden", "");
                }
            });
        });

        // Keyboard: arrow keys to switch tabs
        tab.addEventListener("keydown", (e) => {
            if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                const idx = Array.from(tabs).indexOf(tab);
                const next =
                    e.key === "ArrowRight"
                        ? tabs[(idx + 1) % tabs.length]
                        : tabs[(idx - 1 + tabs.length) % tabs.length];
                next.click();
                next.focus();
            }
        });
    });
});
