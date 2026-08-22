document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("contactForm");
    const msg = document.getElementById("contactMsg");

    if (!form || !msg) {
        return;
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const name = document.getElementById("contactName").value.trim();
        const mobile = document.getElementById("contactMobile").value.trim();
        const email = document.getElementById("contactEmail").value.trim();
        const message = document.getElementById("contactMessage").value.trim();

        if (!name || !mobile || !email) {
            msg.innerHTML = `
                <div class="form-msg error">
                    Please fill in your name, mobile number, and email.
                </div>
            `;
            return;
        }

        const entries = JSON.parse(
            localStorage.getItem("contactMessages") || "[]"
        );

        entries.push({
            name,
            mobile,
            email,
            message,
            date: new Date().toISOString()
        });

        localStorage.setItem(
            "contactMessages",
            JSON.stringify(entries)
        );

        msg.innerHTML = `
            <div class="form-msg success">
                Thanks, ${name}! We've received your message and will get back to you soon.
            </div>
        `;

        form.reset();
    });
});