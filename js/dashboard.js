document.addEventListener("DOMContentLoaded", () => {
    const session = requireAuth();

    if (!session) {
        return;
    }

    const users = getUsers();

    const user = users.find(
        (u) => u.email.toLowerCase() === session.email.toLowerCase()
    );

    const greeting = document.getElementById("dashGreeting");

    if (greeting) {
        greeting.textContent = `Welcome back, ${
            user ? user.name : session.email
        }`;
    }

    const accounts = getAccountsForUser(session.email);
    const root = document.getElementById("dashRoot");

    if (!root) {
        return;
    }

    if (accounts.length === 0) {
        root.innerHTML = `
            <div class="empty-state">
                <h2>No challenge accounts yet</h2>
                <p>
                    Buy a challenge to see your simulated account here.
                </p>

                <a
                    href="pricing.html"
                    class="btn btn-primary"
                    style="margin-top:16px;"
                >
                    View Plans
                </a>
            </div>
        `;

        return;
    }

    // Show the user's most recently created account.
    const account = accounts[accounts.length - 1];

    // Static mock payout history for demo purposes.
    const payoutHistory = [
        {
            date: "2026-07-02",
            amount: Math.round(account.accountSize * 0.06),
            status: "paid"
        },
        {
            date: "2026-07-18",
            amount: Math.round(account.accountSize * 0.04),
            status: "paid"
        },
        {
            date: "2026-08-01",
            amount: Math.round(account.accountSize * 0.05),
            status: "active"
        }
    ];

    root.innerHTML = `
        <div class="dash-grid">

            <div class="dash-card">
                <div class="label">Account Size</div>
                <div class="value">
                    ${formatINR(account.accountSize)}
                </div>
            </div>

            <div class="dash-card">
                <div class="label">Simulated Balance</div>
                <div class="value pos">
                    ${formatINR(account.balance)}
                </div>
            </div>

            <div class="dash-card">
                <div class="label">Profit Split</div>
                <div class="value">
                    ${account.profitSplit}%
                </div>
            </div>

            <div class="dash-card">
                <div class="label">Phase</div>
                <div class="phase-pill">
                    ${account.phase}
                </div>
            </div>

        </div>

        <div
            class="section-head"
            style="text-align:left; margin-bottom:20px;"
        >
            <h2 style="font-size:1.3rem;">
                Payout history (mock)
            </h2>
        </div>

        <div
            class="pricing-table-wrap"
            style="margin-bottom:48px;"
        >
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    ${payoutHistory
                        .map(
                            (p) => `
                                <tr>
                                    <td>${p.date}</td>

                                    <td>
                                        ${formatINR(p.amount)}
                                    </td>

                                    <td>
                                        <span class="status-pill ${p.status}">
                                            ${
                                                p.status === "paid"
                                                    ? "Paid"
                                                    : "Processing"
                                            }
                                        </span>
                                    </td>
                                </tr>
                            `
                        )
                        .join("")}
                </tbody>
            </table>
        </div>
    `;
});