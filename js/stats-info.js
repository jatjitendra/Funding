document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("payoutInfoBtn");
    const popover = document.getElementById("payoutInfoPopover");
    const card = button ? button.closest(".stat-card") : null;

    if (!button || !popover || !card) {
        return;
    }

    function openPopover() {
        button.classList.add("open");
        popover.classList.add("open");
        button.setAttribute("aria-expanded", "true");
    }

    function closePopover() {
        button.classList.remove("open");
        popover.classList.remove("open");
        button.setAttribute("aria-expanded", "false");
    }

    // Desktop: show on hover and focus.
    button.addEventListener("mouseenter", openPopover);
    button.addEventListener("focus", openPopover);

    card.addEventListener("mouseleave", closePopover);
    button.addEventListener("blur", closePopover);

    // Touch devices have no hover, so tap toggles the popover.
    button.addEventListener("click", (event) => {
        event.stopPropagation();

        if (popover.classList.contains("open")) {
            closePopover();
        } else {
            openPopover();
        }
    });

    // Close when clicking outside the card.
    document.addEventListener("click", (event) => {
        if (!card.contains(event.target)) {
            closePopover();
        }
    });
});