"""End-to-end smoke test against a running server.

    python scripts/smoke_test.py [--base-url http://127.0.0.1:8000]

Walks the same path a visitor takes through the frontend: browse plans, sign up,
buy a challenge, read the dashboard, send a contact message.
"""

from __future__ import annotations

import argparse
import sys
import uuid

import httpx

PASS = "PASS"
FAIL = "FAIL"

failures: list[str] = []


def check(name: str, condition: bool, extra: str = "") -> None:
    status = PASS if condition else FAIL

    if not condition:
        failures.append(name)

    print(f"[{status}] {name}{f' — {extra}' if extra else ''}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    api = args.base_url.rstrip("/") + "/api"
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"

    with httpx.Client(timeout=20.0) as client:
        response = client.get(f"{api}/health")
        check("health returns ok", response.status_code == 200 and response.json()["status"] == "ok")

        response = client.get(f"{api}/plans")
        plans = response.json()
        check("three seeded plans", response.status_code == 200 and len(plans) == 3, f"got {len(plans)}")
        check(
            "plan JSON uses frontend keys",
            {"accountSize", "profitSplit", "evalLabel", "phase1ProfitPct", "mostPopular"} <= set(plans[0]),
        )

        response = client.get(f"{api}/plans/does-not-exist")
        check("unknown plan is 404", response.status_code == 404)

        response = client.get(f"{api}/accounts")
        check("dashboard requires auth", response.status_code == 401)

        response = client.post(
            f"{api}/auth/signup",
            json={"name": "Smoke Tester", "email": email, "password": "secret123"},
        )
        check("signup returns 201 + token", response.status_code == 201 and "token" in response.json())
        token = response.json()["token"]
        auth = {"Authorization": f"Bearer {token}"}

        response = client.post(
            f"{api}/auth/signup",
            json={"name": "Duplicate", "email": email.upper(), "password": "secret123"},
        )
        check(
            "duplicate email rejected case-insensitively",
            response.status_code == 409,
            response.json().get("detail", ""),
        )

        response = client.post(f"{api}/auth/signup", json={"name": "Shorty", "email": "s@e.com", "password": "123"})
        check("short password rejected", response.status_code == 422)

        response = client.post(f"{api}/auth/login", json={"email": email, "password": "wrong"})
        check("bad password rejected", response.status_code == 401, response.json().get("detail", ""))

        response = client.post(f"{api}/auth/login", json={"email": email.upper(), "password": "secret123"})
        check("login succeeds", response.status_code == 200 and "token" in response.json())

        response = client.get(f"{api}/auth/me", headers=auth)
        check("me returns the signed-in user", response.status_code == 200 and response.json()["email"] == email)

        response = client.get(f"{api}/auth/me", headers={"Authorization": "Bearer not-a-token"})
        check("garbage token rejected", response.status_code == 401)

        response = client.get(f"{api}/accounts", headers=auth)
        check("new user has no accounts", response.status_code == 200 and response.json() == [])

        response = client.get(f"{api}/accounts/latest", headers=auth)
        check("empty dashboard is 404", response.status_code == 404)

        plan = next(item for item in plans if item["id"] == "two-step-20000")
        card = {
            "cardName": "Smoke Tester",
            "cardNumber": "4242 4242 4242 4242",
            "cardExpiry": "12/34",
            "cardCvc": "123",
        }

        response = client.post(
            f"{api}/checkout",
            headers=auth,
            json={"planId": plan["id"], "fullName": "Smoke Tester", "agreeRules": False, **card},
        )
        check("checkout without agreeing is rejected", response.status_code == 422)

        response = client.post(
            f"{api}/checkout",
            headers=auth,
            json={
                "planId": plan["id"],
                "fullName": "Smoke Tester",
                "agreeRules": True,
                **{**card, "cardNumber": "1234 5678 9012 3456"},
            },
        )
        check("invalid card number is rejected", response.status_code == 422, response.json().get("detail", ""))

        response = client.post(
            f"{api}/checkout",
            headers=auth,
            json={"planId": plan["id"], "fullName": "Smoke Tester", "agreeRules": True, **{**card, "cardExpiry": "01/20"}},
        )
        check("expired card is rejected", response.status_code == 422, response.json().get("detail", ""))

        response = client.post(
            f"{api}/checkout",
            headers=auth,
            json={"planId": plan["id"], "fullName": "Smoke Tester", "agreeRules": True, **card},
        )
        check("checkout succeeds", response.status_code == 201, response.text[:160])
        body = response.json()
        account_id = body["account"]["id"]
        check("account opens at the plan's size", body["account"]["accountSize"] == plan["accountSize"])
        check("account starts in Step 1", body["account"]["phase"] == "Step 1")
        check("balance seeded from account size", float(body["account"]["balance"]) == float(plan["accountSize"]))
        check("order charges the plan price", float(body["order"]["amount"]) == float(plan["price"]))
        check("only last4 of the card is stored", body["order"]["cardLast4"] == "4242")
        check("three payout rows created", len(body["payouts"]) == 3)

        response = client.get(f"{api}/accounts/latest", headers=auth)
        check("dashboard shows the new account", response.status_code == 200 and response.json()["id"] == account_id)

        response = client.get(f"{api}/accounts/{account_id}/payouts", headers=auth)
        payouts = response.json()
        check("payout history readable", response.status_code == 200 and len(payouts) == 3)
        check(
            "payout rows carry date/amount/status",
            all({"date", "amount", "status"} <= set(row) for row in payouts),
        )

        response = client.get(f"{api}/accounts/{account_id + 10_000}", headers=auth)
        check("someone else's account is 404", response.status_code == 404)

        response = client.get(f"{api}/checkout/orders", headers=auth)
        check("order history readable", response.status_code == 200 and len(response.json()) == 1)

        response = client.post(
            f"{api}/contact",
            json={"name": "Smoke", "mobile": "+91 98765 43210", "email": email, "message": "Hello"},
        )
        check("contact form accepted", response.status_code == 201 and "Thanks, Smoke!" in response.json()["message"])

        response = client.post(f"{api}/contact", json={"name": "", "mobile": "", "email": "nope"})
        check("empty contact form rejected", response.status_code == 422)

        response = client.get(f"{api}/contact", headers=auth)
        check("contact inbox requires auth and lists messages", response.status_code == 200 and response.json())

        response = client.get(f"{api}/stats")
        stats = response.json()
        check(
            "stats expose the homepage numbers",
            response.status_code == 200 and stats["profitSplit"] == 80 and stats["accountsFunded"] >= 10,
        )

        response = client.get(f"{api}/market/tickers")
        check("market proxy responds", response.status_code == 200 and "tickers" in response.json())

        response = client.post(f"{api}/auth/logout", headers=auth)
        check("logout returns 204", response.status_code == 204)

        response = client.get(f"{args.base_url.rstrip('/')}/")
        check("frontend index served", response.status_code == 200 and "ApexFund" in response.text)

        response = client.get(f"{args.base_url.rstrip('/')}/css/style.css")
        check("stylesheet served", response.status_code == 200)

    print()

    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
