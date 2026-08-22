document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("checkoutRoot");
    const params = new URLSearchParams(window.location.search);

    const plan = getPlanById(params.get("plan"));

    if (!plan) {
        root.innerHTML = `
            <div class="empty-state">
                <h2>Plan not found</h2>
                <p>Pick a challenge from the pricing page to continue.</p>

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

    const session = getSession();

    if (!session) {
        const next = encodeURIComponent(
            `checkout.html?plan=${plan.id}`
        );

        root.innerHTML = `
            <div class="empty-state">
                <h2>Log in to continue</h2>

                <p>
                    You need an account before buying the
                    ${plan.evalLabel} ${formatINR(plan.accountSize)}
                    challenge.
                </p>

                <div
                    style="
                        display:flex;
                        gap:12px;
                        justify-content:center;
                        margin-top:16px;
                    "
                >
                    <a
                        href="login.html?next=${next}"
                        class="btn btn-outline"
                    >
                        Log In
                    </a>

                    <a
                        href="signup.html?next=${next}"
                        class="btn btn-primary"
                    >
                        Sign Up
                    </a>
                </div>
            </div>
        `;

        return;
    }

    root.innerHTML = `
        <div class="section-head">
            <span class="eyebrow">Challenge Rules</span>

            <h2>
                ${plan.evalLabel}
                &ndash;
                ${formatINR(plan.accountSize)}
                Demo Account
            </h2>

            <p>
                Both phases below are evaluated on a simulated demo account
                of ${formatINR(plan.accountSize)}.
            </p>
        </div>

        <div class="phase-grid">

            <div class="dash-card">
                <div class="label">Phase 1</div>

                <div class="value">
                    ${plan.phase1ProfitPct}% Profit Target
                </div>

                <p>
                    Max daily loss: ${plan.maxDailyLossPct}%
                    &middot;
                    Max total loss: ${plan.maxTotalLossPct}%
                    &middot;
                    No time limit
                </p>
            </div>

            <div class="dash-card">
                <div class="label">Phase 2</div>

                <div class="value">
                    ${plan.phase2ProfitPct}% Profit Target
                </div>

                <p>
                    Max daily loss: ${plan.maxDailyLossPct}%
                    &middot;
                    Max total loss: ${plan.maxTotalLossPct}%
                    &middot;
                    No time limit
                </p>
            </div>

        </div>

        <div
            class="section-head"
            style="margin-top:48px;"
        >
            <span class="eyebrow">Checkout</span>
            <h2>Complete your challenge purchase</h2>
        </div>

        <div class="checkout-grid">

            <div>

                <div id="formMsg"></div>

                <form id="checkoutForm">

                    <div class="field">
                        <label for="fullName">Full name</label>

                        <input
                            type="text"
                            id="fullName"
                            required
                            value="${session.email.split("@")[0]}"
                        >
                    </div>

                    <div class="field">
                        <label for="buyerEmail">Email</label>

                        <input
                            type="email"
                            id="buyerEmail"
                            value="${session.email}"
                            readonly
                        >
                    </div>

                    <label class="field-check">
                        <input
                            type="checkbox"
                            id="agreeRules"
                            required
                        >

                        <span>
                            I have read all the rules for Phase 1 and
                            Phase 2 above.
                        </span>
                    </label>

                    <div class="field">
                        <label for="cardName">Name on card</label>

                        <input
                            type="text"
                            id="cardName"
                            required
                            value="${session.email.split("@")[0]}"
                        >
                    </div>

                    <div class="field">
                        <label for="cardNumber">Card number</label>

                        <input
                            type="text"
                            id="cardNumber"
                            required
                            placeholder="4242 4242 4242 4242"
                            maxlength="19"
                        >
                    </div>

                    <div style="display:flex; gap:14px;">

                        <div
                            class="field"
                            style="flex:1;"
                        >
                            <label for="cardExp">Expiry</label>

                            <input
                                type="text"
                                id="cardExp"
                                required
                                placeholder="MM/YY"
                                maxlength="5"
                            >
                        </div>

                        <div
                            class="field"
                            style="flex:1;"
                        >
                            <label for="cardCvc">CVC</label>

                            <input
                                type="text"
                                id="cardCvc"
                                required
                                placeholder="123"
                                maxlength="4"
                            >
                        </div>

                    </div>

                    <button
                        type="submit"
                        class="btn btn-primary btn-block"
                        id="payBtn"
                        disabled
                    >
                        Pay ${formatINR(plan.price)} (Simulated)
                    </button>

                </form>

            </div>

            <div class="summary-card">

                <h3>Order Summary</h3>

                <div class="summary-row">
                    <span>Evaluation type</span>
                    <strong>${plan.evalLabel}</strong>
                </div>

                <div class="summary-row">
                    <span>Account size</span>
                    <strong>${formatINR(plan.accountSize)}</strong>
                </div>

                <div class="summary-row">
                    <span>Profit split</span>
                    <strong>${plan.profitSplit}%</strong>
                </div>

                <div class="summary-row">
                    <span>Buyer</span>
                    <strong>${session.email}</strong>
                </div>

                <div class="summary-total">
                    <span>Total</span>
                    <span>${formatINR(plan.price)}</span>
                </div>

            </div>

        </div>
    `;

    const agreeCheckbox = document.getElementById("agreeRules");
    const payBtn = document.getElementById("payBtn");
    const checkoutForm = document.getElementById("checkoutForm");

    agreeCheckbox.addEventListener("change", () => {
        payBtn.disabled = !agreeCheckbox.checked;
    });

    checkoutForm.addEventListener("submit", (e) => {
        e.preventDefault();

        if (!agreeCheckbox.checked) {
            return;
        }

        createAccount({
            email: session.email,
            plan: plan
        });

        window.location.href = "dashboard.html";
    });
});