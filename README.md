This is stripe-inspired payment platform to understand how production-grade payment systems are designed, not a real payment processor and not intended for real transactions.

Sign up as a merchant, get sandboxed API keys, and integrate them into your own website to accept payments. Includes a merchant dashboard for monitoring payments, refunds, payouts, and customers — the same shape a real payment provider's dashboard takes.


## 1. Running it locally (Windows)

### Prerequisites (must be running before anything else)

- PostgreSQL: running as a Windows service (services.msc → postgresql-x64-...)
- Memurai ("Redis" for Windows, kinda): running as a Windows service (services.msc → Memurai)
- A `.env` file in `backend/`: git-ignored, not in the repo, must exist locally. Required keys: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `API_KEY_PEPPER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`

### One-time setup

```
cd backend
venv\Scripts\activate
alembic upgrade head
```

### Three terminals, every time you run it

**Terminal 1: API server**

```
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Interactive API docs (auto-generated from the actual schemas): http://localhost:8000/docs

**Terminal 2: Celery worker + beat**

```
cd backend
venv\Scripts\activate
celery -A app.core.celery_app worker --beat --loglevel=info --pool=solo
```

**Terminal 3: Frontend**

```
cd frontend
npm run dev
```

## 2. Getting API keys

There are always **two keys per mode**, a publishable key (`pk_`) and a secret
key (`sk_`). This split exists so raw card data never has to touch
your own server-side application.

### Test keys: Available immediately, no approval needed
1. Sign up, and use an actual email address to receive the verification code.
2. Log in, create a merchant profile (`POST /api/v1/merchants`) if you haven't.
3. Go to **API Keys** in the dashboard (or `GET /api/v1/merchants/me/api-keys`).
   A `pk_test_...` / `sk_test_...` pair is generated automatically with the merchant.
4. **Copy both now** because the secret key is shown once and never again. If lost,
   your only recovery is `POST /api/v1/merchants/me/test-keys/regenerate`, which
   immediately revokes the current active test pair before issuing a new one.

Use test keys for everything. Sandbox decline behavior is controlled by
the payment amount, not the card number.

- **The card number itself carries no meaning here.** `4242424242424242` isn't
  special, it's just a Visa-shaped string that passes the `card_number`
  validator (digits only, 12-19 characters). You could type any digit string
  of the right length and it would tokenize identically. This is unlike some
  real sandboxes (Stripe's real test mode included) where *specific* card
  numbers are reserved to trigger specific outcomes. Here, the card number
  is not the lever.
- **The amount is the lever.** Whether a payment approves, declines, or times
  out is decided entirely by the last two digits of `amount_minor` (`...00`/`...01`/`...02`/`...03`). So to deliberately test a decline path, you don't swap the card, you change what you're charging.
- **Practical implication for your integration:** product prices are often
  fixed, round numbers (e.g. an order for 18,000.00 → `amount_minor` ending
  in `00`, which always approves). To actually exercise a decline in your
  checkout flow, you need to either temporarily adjust a test order's amount
  to end in `.01`/`.02`/`.03`, or add a small adjustable test surcharge during
  development, since there's no other way to reach those code paths through
  a normal purchase.
- **Why this matters beyond just testing:** it means your integration's error
  handling (the "declined" and "processing" branches of your checkout logic)
  can only be verified by *engineering* the amount, not by picking a "bad"
  test card. If you only ever check out at round numbers, you will never see
  a decline in this system, and a checkout flow that "always works" in your
  own testing isn't actually proof those branches are correct.

### Live keys: Require KYC approval, and require an admin account
This is the one part of the flow that isn't self-service by design. Mirroring
how real payment providers gate real money behind identity verification. As a
solo developer running this locally, you'll need to act as your own admin to
get through it. Steps:

1. **Set settlement bank details** (required before KYC can be submitted):
   ```
   PUT /api/v1/merchants/me/settlement-details
   ```
2. **Submit for KYC review** — moves the merchant from `pending` to `under_review`:
   ```
   POST /api/v1/merchants/me/submit-kyc
   ```
3. **Approve it as an admin.** There is no self-service way to become an admin —
   `role` defaults to `merchant_owner` on every normal signup. You need a user
   row with `role = admin` in Postgres directly (via a one-off script, or a
   direct `UPDATE users SET role = 'admin' WHERE email = '...'`). Once you have
   admin credentials, log in as that admin and call:
   ```
   POST /api/v1/admin/merchants/{merchant_id}/verify
   { "approved": true }
   ```
4. **Issue the live key pair**, back as the merchant user:
   ```
   POST /api/v1/merchants/me/live-keys
   ```
   Returns 403 if `kyc_status` isn't `approved` yet.

Note: nothing about "live" keys makes them talk to a real processor. The
sandbox adapter is used regardless of test/live mode in this project. Live mode
here only changes the *authorization gate* (KYC), not the underlying execution.

---

## 3. Integrating into your own application

Base URL locally: `http://localhost:8000`. Not deployed anywhere. Everything
below is plain HTTP/JSON. No SDK exists for this project, so any language or
framework that can make an HTTP request and parse JSON can integrate.

### The shape of the integration
Your integration needs **two sides**, because the two keys are used by two
different callers, regardless of what language either side is written in:

| Step | Caller | Key | Endpoint |
|---|---|---|---|
| 1. Create a payment intent | Your server-side application | `sk_` | `POST /api/v1/payments/payment-intents` |
| 2. Tokenize the card | The customer's browser | `pk_` | `POST /api/v1/checkout/payment-methods` |
| 3. Confirm the intent | The customer's browser | `pk_` + `client_secret` | `POST /api/v1/checkout/payment-intents/{id}/confirm?client_secret=...` |

Auth header on every call, using the actual key format. Merchant-scoped calls
use `sk_`, browser calls use `pk_`:
```
Authorization: Bearer sk_test_6Zc-kpvKdBYRKywc_B6s4IbY8Dahw8cmZObUCtV7N_M
```

**Step 1 — create intent.** Request body:
```json
{
  "amount_minor": 5000,
  "currency": "kes",
  "customer_id": null,
  "description": "Order #1234",
  "idempotency_key": "order-1234-attempt-1"
}
```
`amount_minor` is the smallest currency unit (cents), not a decimal amount.
Response (`PaymentIntentResponse` — note `client_secret` is only ever included
in *this* shape, returned to your `sk_`-authenticated backend, never sent to
the browser directly by this endpoint):
```json
{
  "id": "5f3a1c2e-...-9b21",
  "customer_id": null,
  "amount_minor": 5000,
  "currency": "KES",
  "status": "requires_payment_method",
  "description": "Order #1234",
  "failure_reason": null,
  "is_live_mode": "test",
  "client_secret": "pi_5f3a1c2e_secret_a91f...",
  "created_at": "2026-08-04T10:15:00Z",
  "updated_at": "2026-08-04T10:15:00Z"
}
```
Your server-side application passes `id` and `client_secret` to the browser from here — how you do that (a template variable, a JSON API response, a session) is entirely up to your stack.

**Step 2 — tokenize card.** Request body, raw card details, straight from the
browser, never through your own server:
```json
{ "card_number": "4242424242424242", "exp_month": 12, "exp_year": 2027, "cvv": "123" }
```
`cvv`, not `cvc`, a real mismatch hit while building this. `card_number`
spaces/dashes are actually stripped server-side too (`digits_only` validator
in `TokenizeCardRequest`), so stripping client-side is optional belt-and-braces,
not strictly required. Response (`PaymentMethodResponse`) — note the raw card number is never echoed
back, only a token id and the last 4 digits:
```json
{
  "id": "8a1e...-pm",
  "card_brand": "visa",
  "card_last4": "4242",
  "card_exp_month": 12,
  "card_exp_year": 2027,
  "created_at": "2026-08-04T10:15:04Z"
}
```
`id` here is the `payment_method_id` step 3 needs.

**Step 3 — confirm.** `client_secret` is a **query parameter**, not a body field:
```
POST /api/v1/checkout/payment-intents/{id}/confirm?client_secret=pi_5f3a1c2e_secret_a91f...
```
Body:
```json
{ "payment_method_id": "8a1e...-pm" }
```
This proves the calling browser is the one the intent was actually created for
— `pk_` alone isn't scoped to a single intent, so without this check, anyone
with your `pk_` could confirm any of your intents by guessing an ID.

### Reading the response — this is the most important integration detail
A card **decline is still HTTP 200**. Only genuine request errors (bad state,
not-found, validation failures) return 4xx. Always check the `status` field in
the body, never `response.ok` / the HTTP status code alone:
```json
{ "id": "...", "status": "succeeded", "amount_minor": 5000, "currency": "KES", "failure_reason": null, ... }
{ "id": "...", "status": "declined", "failure_reason": "insufficient_funds", ... }
{ "id": "...", "status": "processing", "failure_reason": null, ... }
```
`"processing"` means the payment was either timed out by the sandbox processor,
or held for manual fraud review (see §4) — your UI needs a path for this state,
not just succeeded/declined.

### Error format
There's no custom exception handling anywhere in this API (`main.py` has none) —
every error is FastAPI's default shape, always under a `detail` key, but the
*value* differs by error type. There is no `{"error": {"code": ..., "message": ...}}`
form anywhere in this codebase.

Business-logic errors (400/403/404) — `detail` is a plain string:
```json
{ "detail": "Cannot confirm a payment intent in status 'succeeded'" }
```
Request validation errors (422) — `detail` is an array, one entry per bad field:
```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "cvv"], "msg": "Field required", "input": { "...": "..." } }
  ]
}
```
So: check whether `detail` is a string or an array before deciding how to
display it — a naive `err.response.data.detail` rendered directly will break
on a 422 (an array rendered as a UI string is a real bug this project hit).

### Idempotency
Yes — sending the same `idempotency_key` twice returns the **original** payment
intent, not a new one. Verified directly in `PaymentService.create_intent`: it
looks up an existing intent by `(merchant_id, idempotency_key)` first, and only
creates a new row if none is found. Safe to retry a create-intent call after a
network timeout without risking a duplicate intent — this is a real guarantee,
not just a stored, unused field.

### Currency support
No whitelist — `currency` is validated only as an exactly-3-character string
(`Field(min_length=3, max_length=3)`) and uppercased on save. `"usd"`, `"eur"`,
or even a made-up 3-letter code would all be accepted; there's no real ISO-4217
validation or per-merchant currency restriction. Worth treating as "any 3-letter
code is technically accepted" rather than "USD/EUR are supported" — the system
doesn't actually know what a real currency is.

### Integration flow, language-agnostic

The three calls below are plain HTTP — this is the sequence regardless of
whether your server-side application is Node, PHP, Ruby, Java, Go, or anything
else, and regardless of whether the browser-side code is vanilla JS, a
framework, or a mobile WebView.

1. **Your server-side application** sends a request (any HTTP client library)
   to `POST /api/v1/payments/payment-intents` with `sk_` in the `Authorization`
   header and the JSON body from Step 1 above. It receives back `id` and
   `client_secret`, and passes both to the browser however your stack renders
   pages or returns API responses (server-rendered template variable, a JSON
   endpoint your frontend calls, etc.).
2. **The browser** sends a request to `POST /api/v1/checkout/payment-methods`
   with `pk_` in the `Authorization` header and the card fields from Step 2
   above. It receives back a `payment_method_id`.
3. **The browser** sends a request to
   `POST /api/v1/checkout/payment-intents/{id}/confirm?client_secret=...`
   with `pk_` in the header, the `client_secret` from step 1 as a query
   parameter, and `{ "payment_method_id": ... }` as the body.
4. **The browser reads `status` from the response** — `succeeded`, `declined`,
   or `processing` — and shows the customer the corresponding outcome. It does
   **not** treat `status === "succeeded"` alone as proof the order should be
   fulfilled (see Webhook payload, below) — that decision belongs on your
   server, driven by a verified webhook, not by trusting whatever the browser
   reports back.

Any HTTP client can perform steps 1-3 — a curl command, `fetch`, `axios`,
`requests`, `HttpClient`, whatever your language provides. The requirements
are only ever: right method, right URL, right key in the `Authorization`
header, right JSON body/query param as documented above.

### Webhook payload
Register a webhook URL under **Webhooks** in the dashboard. Delivery depends
entirely on Terminal 2 (Celery beat) running a 15-second sweep — the "deliver
immediately on event" path exists as a task (`deliver_webhook_task`) but is
never actually called from `emit_event`, so in practice every webhook, first
attempt included, is picked up on the next beat tick, not instantly.

Every delivery POSTs this exact body (`webhook_service.attempt_delivery`):
```json
{
  "id": "evt_...",
  "type": "payment_intent.succeeded",
  "created_at": "2026-08-04T10:15:07Z",
  "data": {
    "payment_intent_id": "5f3a1c2e-...-9b21",
    "amount_minor": 5000,
    "currency": "KES"
  }
}
```
Headers on the request: `X-PayFlow-Signature` (HMAC-SHA256 of the raw JSON body,
using your endpoint's `whsec_...`) and `X-PayFlow-Event-Type`. Verify the
signature before trusting the payload — this is the actual source of truth for
order fulfillment, not the synchronous confirm response, which can be lost to
a network blip even after a real success.

---

## 4. Sandbox processor rules

No real card network is connected. `authorize()` decides approve/decline based
on the **last two digits of the amount**:
- `...00` (or any other ending) → approved
- `...01` → declined, insufficient funds
- `...02` → declined, card blocked
- `...03` → times out (`status` stays `processing`)

### Fraud gate (runs before every authorization attempt)
- **Velocity check:** more than 3 confirm attempts on the same tokenized card
  within a 10-minute window forces the payment into manual review
  (`status: "processing"`, no processor call made yet).
- **Risk score ≥ 50** (new customer, no customer, billing-country mismatch,
  high value ≥ KES 20,000, velocity exceeded) also forces manual review.
- Manual review is resolved by an admin: `GET /api/v1/fraud/cases/pending`,
  then `POST /api/v1/fraud/cases/{case_id}/decide { "approved": true|false }`.

---

It should work, i guess

