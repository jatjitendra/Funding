# ApexFund Backend

FastAPI backend for the ApexFund demo funded-trading site that lives in the
repository root. The static frontend faked everything in `localStorage`; this
service replaces each of those behaviours with real, persisted endpoints.

Like the frontend, it is a demo: no payment gateway is contacted, no brokerage
exists, and card numbers are validated then discarded.

## Quick start

```bash
cd backend_jitendra
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # optional; sensible defaults apply without it
uvicorn app.main:app --reload --port 8000
```

Then open:

| URL | What it is |
| --- | --- |
| <http://127.0.0.1:8000/> | The frontend, served by this process |
| <http://127.0.0.1:8000/api/docs> | Interactive Swagger UI |
| <http://127.0.0.1:8000/api/health> | Health check |

Tables are created and the three challenge plans are seeded automatically on
startup. With no `DATABASE_URL` set, data goes to `backend_jitendra/apexfund.db`
(SQLite), so there is nothing to install.

To confirm the whole flow works, with the server running:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

## What replaces what

| Frontend behaviour | Previously | Now |
| --- | --- | --- |
| `signup()` / `login()` / `getSession()` in `js/auth.js` | `localStorage` user array, plaintext passwords | `POST /api/auth/signup`, `/login`, `GET /me`, JWT + PBKDF2 hashes |
| `PLANS` array in `js/data.js` | Hard-coded in JS | `GET /api/plans` from the `plans` table |
| `createAccount()` on checkout | `localStorage` record | `POST /api/checkout` writes an order, an account and its payouts |
| Dashboard cards in `js/dashboard.js` | Read `localStorage` | `GET /api/accounts/latest` |
| Dashboard payout table | Hard-coded array in JS | `GET /api/accounts/{id}/payouts` |
| Contact form in `js/contact.js` | `localStorage.contactMessages` | `POST /api/contact` |
| Ticker in `js/market-ticker.js` | Browser called Binance directly | `GET /api/market/tickers` proxies and caches it |
| Homepage stat cards | Hard-coded HTML | `GET /api/stats` |

## API

All routes are under `/api`. Protected routes need `Authorization: Bearer <token>`.

### Auth

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/api/auth/signup` | – | `{name, email, password}`; 409 if the email is taken, 422 if the password is under 6 characters |
| POST | `/api/auth/login` | – | `{email, password}`; 401 on bad credentials |
| GET | `/api/auth/me` | yes | The signed-in user |
| POST | `/api/auth/logout` | yes | 204; tokens are stateless, so the client discards its own |

Emails are matched case-insensitively, mirroring the frontend's
`email.toLowerCase()` comparisons. Signup and login both return
`{token, tokenType, expiresIn, user}`.

### Plans

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/plans` | – |
| GET | `/api/plans/{plan_id}` | – |

### Accounts

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/accounts` | yes | Every account belonging to the caller |
| GET | `/api/accounts/latest` | yes | Most recent account, which is what the dashboard shows; 404 when the user has none |
| GET | `/api/accounts/{id}` | yes | 404 for accounts owned by someone else |
| GET | `/api/accounts/{id}/payouts` | yes | Payout history |

### Checkout

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/api/checkout` | yes | Creates the order, account and payout rows in one transaction |
| GET | `/api/checkout/orders` | yes | The caller's purchase history |

Request body:

```json
{
  "planId": "two-step-20000",
  "fullName": "Jitendra Kumar",
  "agreeRules": true,
  "cardName": "Jitendra Kumar",
  "cardNumber": "4242 4242 4242 4242",
  "cardExpiry": "12/34",
  "cardCvc": "123"
}
```

`agreeRules` must be `true`, the card number must pass a Luhn check, and the
expiry must not be in the past. The response returns the order, the new account
and its payout rows.

### Contact, stats, market

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/api/contact` | – | Returns the same thank-you copy the frontend used to render |
| GET | `/api/contact` | yes | Inbox; protected because submissions carry personal details |
| GET | `/api/stats` | – | Homepage stat card numbers |
| GET | `/api/market/tickers?symbols=BTCUSDT,ETHUSDT` | – | Cached Binance Futures proxy |

The market response includes `available`. When the upstream call fails the
endpoint still returns 200 with the last cached values and `available: false`,
which is the signal `js/market-ticker.js` uses to show "Live (unavailable)".

## Wiring the frontend to it

Responses are serialised in camelCase, so the keys already match what the
existing JavaScript reads (`accountSize`, `profitSplit`, `planId`, `evalLabel`,
`phase1ProfitPct`, and so on). Two things change in the frontend when you switch
it over:

1. Store the JWT instead of a session object. `js/auth.js` keeps
   `apexfund_session`; put `{token, user}` there and send the token as a bearer
   header.
2. Errors arrive as HTTP status codes with a `detail` string rather than
   `{ok: false, error}`. For example, in `login.html`:

```js
const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
});

const body = await response.json();

if (!response.ok) {
    msg.innerHTML = `<div class="form-msg error">${body.detail}</div>`;
    return;
}

localStorage.setItem("apexfund_session", JSON.stringify(body));
```

Validation failures (422) are flattened so `detail` is always a single
human-readable sentence, with the full field-by-field list in `errors`.

## Configuration

Every variable is optional; see `.env.example`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | SQLite file in this folder | Use `postgresql+psycopg://user:pass@host:5432/apexfund` for Postgres |
| `SECRET_KEY` | `dev-secret-change-me` | JWT signing key — **must** be changed outside local development |
| `ACCESS_TOKEN_TTL_MINUTES` | `10080` (7 days) | Token lifetime |
| `SERVE_FRONTEND` | `true` | Serve the static site from this process |
| `FRONTEND_DIR` | repository root | Where the static site lives |
| `CORS_ORIGINS` | common localhost ports | Only needed when the frontend is on another origin |
| `BINANCE_BASE_URL` | `https://fapi.binance.com` | Market data upstream |
| `MARKET_CACHE_SECONDS` | `1.0` | How long ticker responses are reused |

### Switching to Postgres

```bash
createdb apexfund
export DATABASE_URL="postgresql+psycopg://$USER@localhost:5432/apexfund"
uvicorn app.main:app --reload
```

Tables are created on startup, so no migration step is needed. There is no
migration tool wired up yet — worth adding Alembic before any schema changes
land on a database you care about.

## Layout

```
backend_jitendra/
├── app/
│   ├── config.py       Environment-driven settings
│   ├── database.py     Engine, session factory, declarative base
│   ├── models.py       users, plans, accounts, orders, payouts, contact_messages
│   ├── schemas.py      Request/response models and card validation
│   ├── security.py     PBKDF2 password hashing, JWT encode/decode
│   ├── deps.py         get_current_user and the DB session dependency
│   ├── services.py     Account/order/payout creation, stats aggregation
│   ├── seed.py         The three challenge plans from js/data.js
│   ├── main.py         App wiring, error handling, static frontend
│   └── routers/        auth, plans, accounts, checkout, contact, market, stats
├── scripts/
│   └── smoke_test.py   End-to-end check against a running server
├── requirements.txt
└── .env.example
```

## Notes on the demo data

`POST /api/checkout` seeds three payout rows per account at 6%, 4% and 5% of the
account size, dated 30 days before, 14 days before, and on the account's
creation date, with statuses `paid`, `paid` and `processing`. That reproduces the
table `js/dashboard.js` used to hard-code, now from the database.

`GET /api/stats` derives its numbers from real rows but floors them at the values
in the marketing copy (10 accounts funded, ₹100,000 rewards paid) so the
homepage does not read worse than the static site while the database is small.

## Security choices, and what is still missing

Implemented: PBKDF2-SHA256 password hashing (260k iterations, per-user salt),
JWTs with expiry, ownership checks on every account read, identical error copy
for unknown emails and wrong passwords, and card data reduced to the last four
digits before storage.

Not implemented, and needed before this is more than a demo: rate limiting on
the auth and contact endpoints, email verification and password reset, refresh
tokens and revocation, an admin role for the contact inbox (any signed-in user
can read it today), Alembic migrations, and a real payment gateway.

## Caveat on the static file serving

With `SERVE_FRONTEND=true` this process serves `css/`, `js/` and the top-level
`.html` pages from the repository root, and nothing else — `.git`, the SQLite
file and this package are not reachable. It exists so the demo runs from one
command on one origin. In production, put the static site behind a CDN or web
server and set `SERVE_FRONTEND=false`.

The `requirements.txt` in the repository root is the original stub and is now
superseded by the pinned one in this folder.
