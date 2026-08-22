// Simple, client-side-only auth for the ApexFund demo.
//
// Everything lives in localStorage. There is no server and no real security here.
// This exists purely to demonstrate signup/login/dashboard flows for a portfolio project.

const USERS_KEY = "apexfund_users";
const SESSION_KEY = "apexfund_session";
const ACCOUNTS_KEY = "apexfund_accounts";

function getUsers() {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
}

function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function getSession() {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
}

function setSession(email) {
    localStorage.setItem(
        SESSION_KEY,
        JSON.stringify({ email })
    );
}

function logout() {
    localStorage.removeItem(SESSION_KEY);
}

function signup({ name, email, password }) {
    const users = getUsers();

    const exists = users.some(
        (u) => u.email.toLowerCase() === email.toLowerCase()
    );

    if (exists) {
        return {
            ok: false,
            error: "An account with that email already exists."
        };
    }

    users.push({
        name,
        email,
        password
    });

    saveUsers(users);
    setSession(email);

    return {
        ok: true
    };
}

function login({ email, password }) {
    const users = getUsers();

    const user = users.find(
        (u) => u.email.toLowerCase() === email.toLowerCase()
    );

    if (!user || user.password !== password) {
        return {
            ok: false,
            error: "Invalid email or password."
        };
    }

    setSession(email);

    return {
        ok: true
    };
}

function requireAuth() {
    const session = getSession();

    if (!session) {
        window.location.href =
            "login.html?next=" +
            encodeURIComponent(
                window.location.pathname.split("/").pop()
            );

        return null;
    }

    return session;
}

function getAccounts() {
    return JSON.parse(
        localStorage.getItem(ACCOUNTS_KEY) || "[]"
    );
}

function saveAccounts(accounts) {
    localStorage.setItem(
        ACCOUNTS_KEY,
        JSON.stringify(accounts)
    );
}

function getAccountsForUser(email) {
    return getAccounts().filter(
        (a) =>
            a.email.toLowerCase() === email.toLowerCase()
    );
}

function createAccount({ email, plan }) {
    const accounts = getAccounts();

    const record = {
        id: "acc" + Date.now(),
        email,
        planId: plan.id,
        evalLabel: plan.evalLabel,
        accountSize: plan.accountSize,
        profitSplit: plan.profitSplit,
        phase: "Step 1",
        balance: plan.accountSize,
        createdAt: new Date().toISOString()
    };

    accounts.push(record);
    saveAccounts(accounts);

    return record;
}