document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("themeToggle");

    if (!button) {
        return;
    }

    const syncThemeIcon = () => {
        const theme =
            document.documentElement.getAttribute("data-theme") || "dark";

        button.textContent = theme === "dark" ? "☀️" : "🌙";
    };

    button.addEventListener("click", () => {
        const currentTheme =
            document.documentElement.getAttribute("data-theme") || "dark";

        const nextTheme = currentTheme === "dark" ? "light" : "dark";

        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("theme", nextTheme);

        syncThemeIcon();
    });

    // Set the correct icon when the page loads.
    syncThemeIcon();
});