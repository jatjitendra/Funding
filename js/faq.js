document.addEventListener("DOMContentLoaded", () => {
    const faqItems = document.querySelectorAll(".faq-item");

    faqItems.forEach((item) => {
        const question = item.querySelector(".faq-q");
        const answer = item.querySelector(".faq-a");

        if (!question || !answer) {
            return;
        }

        question.addEventListener("click", () => {
            const isOpen = item.classList.contains("open");

            // Close all FAQ items
            faqItems.forEach((other) => {
                other.classList.remove("open");

                const otherAnswer = other.querySelector(".faq-a");

                if (otherAnswer) {
                    otherAnswer.style.maxHeight = null;
                }
            });

            // Open the selected FAQ item
            if (!isOpen) {
                item.classList.add("open");
                answer.style.maxHeight = `${answer.scrollHeight}px`;
            }
        });
    });
});