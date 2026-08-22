const PLANS = [
    {
        id: "two-step-10000",
        evalLabel: "Two-Step Evaluation",
        evalSteps: 2,
        accountSize: 10000,
        originalPrice: 499,
        price: 399,
        profitSplit: 80,
        phase1ProfitPct: 8,
        phase2ProfitPct: 12,
        maxDailyLossPct: 5,
        maxTotalLossPct: 10
    },
    {
        id: "two-step-20000",
        evalLabel: "Two-Step Evaluation",
        evalSteps: 2,
        accountSize: 20000,
        mostPopular: true,
        originalPrice: 799,
        price: 699,
        profitSplit: 80,
        phase1ProfitPct: 8,
        phase2ProfitPct: 12,
        maxDailyLossPct: 5,
        maxTotalLossPct: 10
    },
    {
        id: "two-step-40000",
        evalLabel: "Two-Step Evaluation",
        evalSteps: 2,
        accountSize: 40000,
        originalPrice: 999,
        price: 899,
        profitSplit: 80,
        phase1ProfitPct: 8,
        phase2ProfitPct: 12,
        maxDailyLossPct: 5,
        maxTotalLossPct: 10
    }
];

function getPlanById(id) {
    return PLANS.find((p) => p.id === id) || null;
}

function formatINR(amount) {
    return "₹" + Number(amount).toLocaleString("en-IN");
}