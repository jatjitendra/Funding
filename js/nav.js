document.addEventListener("DOMContentLoaded", () => {
    // Mobile menu toggle
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.addEventListener("click", () => {
            const isOpen = links.classList.toggle("open");
            toggle.innerHTML = isOpen ? "&times;" : "&#9776;";
        });
    }

    // Highlight the active navigation link
    const currentPage =
        window.location.pathname.split("/").pop() || "index.html";

    document.querySelectorAll(".nav-links a").forEach((link) => {
        const target = link.getAttribute("href");

        if (target === currentPage) {
            link.classList.add("active");
        }
    });

    // Auth-aware navigation actions
    const actions = document.getElementById("navActions");

    if (actions && typeof getSession === "function") {
        const session = getSession();

        if (session) {
            actions.innerHTML = `
                <a
                    href="dashboard.html"
                    class="btn btn-outline-light btn-sm nav-hide-mobile"
                >
                    Dashboard
                </a>

                <button
                    id="navLogout"
                    class="btn btn-ghost-light btn-sm"
                    type="button"
                >
                    Logout
                </button>
            `;

            const logoutButton = document.getElementById("navLogout");

            if (logoutButton) {
                logoutButton.addEventListener("click", () => {
                    logout();
                    window.location.href = "index.html";
                });
            }
        } else {
            actions.innerHTML = `
                <a
                    href="login.html"
                    class="btn btn-outline-light btn-sm nav-hide-mobile nav-btn-accent"
                >
                    Login
                </a>

                <a
                    href="signup.html"
                    class="btn btn-outline-light btn-sm nav-hide-mobile"
                >
                    Sign Up
                </a>
            `;
        }
    }
});