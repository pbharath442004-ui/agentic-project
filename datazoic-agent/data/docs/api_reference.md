# API Reference — Datazoic Pay (v2 REST)
One entry per documented endpoint (auto-generated sample corpus; 150 entries).

## API-001 · GET /v2/invoicing/invoices
**Retrieve invoicy data for the Invoicing module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `invoicing:read`, `invoicing:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 51): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/invoicing/invoices
{
  "amount": 39287,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "INV-9271",
  "status": "created",
  "created_at": "2026-09-19T06:31:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 139 req/min per key. Verification on write: schema validation.

## API-002 · GET /v2/invoicing/invoices/items
**Retrieve items data for the Invoicing module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `invoicing:read`, `invoicing:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 169): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/invoicing/invoices/items
{
  "amount": 30024,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "ITE-5342",
  "status": "pending",
  "created_at": "2026-09-19T03:39:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 216 req/min per key. Verification on write: schema validation.

## API-003 · GET /v2/invoicing/invoices/pdf
**Retrieve pdf data for the Invoicing module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `invoicing:read`, `invoicing:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 174): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/invoicing/invoices/pdf
{
  "amount": 55660,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "PDF-1924",
  "status": "active",
  "created_at": "2026-09-19T12:03:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 66 req/min per key. Verification on write: idempotency-key deduplication.

## API-004 · GET /v2/invoicing/invoices/reminders
**Retrieve reminders data for the Invoicing module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `invoicing:read`, `invoicing:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 156): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/invoicing/invoices/reminders
{
  "amount": 7794,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "REM-1985",
  "status": "active",
  "created_at": "2026-09-19T12:28:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 286 req/min per key. Verification on write: signature verification.

## API-005 · POST /v2/invoicing/invoices/summary
**Create or submit a summary record in the Invoicing module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `invoicing:read`, `invoicing:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/invoicing/invoices/summary
{
  "amount": 11402,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SUM-3713",
  "status": "pending",
  "created_at": "2026-09-19T06:11:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 299 req/min per key. Verification on write: idempotency-key deduplication.

## API-006 · GET /v2/payments/payments
**Retrieve payments data for the Payments module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payments:read`, `payments:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 58): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payments/payments
{
  "amount": 41871,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "PAY-7203",
  "status": "pending",
  "created_at": "2026-09-19T10:28:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 87 req/min per key. Verification on write: checksum validation.

## API-007 · POST /v2/payments/payments/cards
**Create or submit a cards record in the Payments module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payments:read`, `payments:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/payments/payments/cards
{
  "amount": 37674,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "CAR-2323",
  "status": "pending",
  "created_at": "2026-09-19T13:56:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 203 req/min per key. Verification on write: schema validation.

## API-008 · GET /v2/payments/payments/bank
**Retrieve bank data for the Payments module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payments:read`, `payments:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 141): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payments/payments/bank
{
  "amount": 41461,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "BAN-8085",
  "status": "created",
  "created_at": "2026-09-19T01:45:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 110 req/min per key. Verification on write: signature verification.

## API-009 · GET /v2/payments/payments/refunds
**Retrieve refunds data for the Payments module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payments:read`, `payments:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 99): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payments/payments/refunds
{
  "amount": 43376,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "REF-6967",
  "status": "succeeded",
  "created_at": "2026-09-19T00:40:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 123 req/min per key. Verification on write: sandbox dry-run.

## API-010 · GET /v2/payments/payments/captures
**Retrieve captury data for the Payments module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payments:read`, `payments:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 60): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payments/payments/captures
{
  "amount": 50226,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CAP-1571",
  "status": "succeeded",
  "created_at": "2026-09-19T02:51:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 125 req/min per key. Verification on write: schema validation.

## API-011 · POST /v2/disputes/disputes
**Create or submit a disputy record in the Disputes module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `disputes:read`, `disputes:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/disputes/disputes
{
  "amount": 80379,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "DIS-6555",
  "status": "pending",
  "created_at": "2026-09-19T08:21:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 71 req/min per key. Verification on write: signature verification.

## API-012 · POST /v2/disputes/disputes/{id}/evidence
**Create or submit a evidence record in the Disputes module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `disputes:read`, `disputes:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `EVI-5515`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/disputes/disputes/{id}/evidence
{
  "amount": 39981,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "EVI-1061",
  "status": "created",
  "created_at": "2026-09-19T00:52:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 87 req/min per key. Verification on write: format validation.

## API-013 · POST /v2/disputes/disputes/{id}/responses
**Create or submit a ryponsy record in the Disputes module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `disputes:read`, `disputes:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `RES-7332`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/disputes/disputes/{id}/responses
{
  "amount": 33905,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "RES-8044",
  "status": "succeeded",
  "created_at": "2026-09-19T04:59:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 106 req/min per key. Verification on write: checksum validation.

## API-014 · GET /v2/disputes/disputes/rules
**Retrieve ruly data for the Disputes module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `disputes:read`, `disputes:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 88): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/disputes/disputes/rules
{
  "amount": 80594,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "RUL-4868",
  "status": "pending",
  "created_at": "2026-09-19T10:29:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 260 req/min per key. Verification on write: idempotency-key deduplication.

## API-015 · POST /v2/disputes/disputes/summary
**Create or submit a summary record in the Disputes module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `disputes:read`, `disputes:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/disputes/disputes/summary
{
  "amount": 68093,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SUM-4232",
  "status": "succeeded",
  "created_at": "2026-09-19T05:15:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 76 req/min per key. Verification on write: sandbox dry-run.

## API-016 · POST /v2/reports/reports/sales
**Create or submit a saly record in the Reports module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reports:read`, `reports:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/reports/reports/sales
{
  "amount": 64136,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SAL-9922",
  "status": "pending",
  "created_at": "2026-09-19T05:27:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 78 req/min per key. Verification on write: signature verification.

## API-017 · POST /v2/reports/reports/revenue
**Create or submit a revenue record in the Reports module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reports:read`, `reports:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/reports/reports/revenue
{
  "amount": 28307,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "REV-2579",
  "status": "succeeded",
  "created_at": "2026-09-19T15:45:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 104 req/min per key. Verification on write: schema validation.

## API-018 · GET /v2/reports/reports/refunds
**Retrieve refunds data for the Reports module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reports:read`, `reports:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 156): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reports/reports/refunds
{
  "amount": 61414,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "REF-4849",
  "status": "created",
  "created_at": "2026-09-19T09:18:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 205 req/min per key. Verification on write: signature verification.

## API-019 · GET /v2/reports/reports/monthly
**Retrieve monthly data for the Reports module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reports:read`, `reports:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 115): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reports/reports/monthly
{
  "amount": 35122,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "MON-4263",
  "status": "succeeded",
  "created_at": "2026-09-19T07:11:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 120 req/min per key. Verification on write: schema validation.

## API-020 · GET /v2/reports/reports/export
**Retrieve export data for the Reports module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reports:read`, `reports:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 198): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reports/reports/export
{
  "amount": 25674,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "EXP-6346",
  "status": "created",
  "created_at": "2026-09-19T12:16:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 189 req/min per key. Verification on write: idempotency-key deduplication.

## API-021 · GET /v2/customers/customers
**Retrieve customers data for the Customers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `customers:read`, `customers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 75): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/customers/customers
{
  "amount": 86632,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CUS-8600",
  "status": "created",
  "created_at": "2026-09-19T03:00:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 286 req/min per key. Verification on write: schema validation.

## API-022 · POST /v2/customers/customers/{id}/balance
**Create or submit a balance record in the Customers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `customers:read`, `customers:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `BAL-7125`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/customers/customers/{id}/balance
{
  "amount": 6290,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "BAL-5811",
  "status": "active",
  "created_at": "2026-09-19T03:03:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 213 req/min per key. Verification on write: idempotency-key deduplication.

## API-023 · GET /v2/customers/customers/{id}/activity
**Retrieve activity data for the Customers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `customers:read`, `customers:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `ACT-2230`)
- `limit` (integer, query, optional, default 20, max 145): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/customers/customers/{id}/activity
{
  "amount": 68196,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "ACT-3912",
  "status": "succeeded",
  "created_at": "2026-09-19T19:16:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 61 req/min per key. Verification on write: checksum validation.

## API-024 · GET /v2/customers/customers/tags
**Retrieve tags data for the Customers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `customers:read`, `customers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 105): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/customers/customers/tags
{
  "amount": 5909,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "TAG-7040",
  "status": "pending",
  "created_at": "2026-09-19T04:02:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 125 req/min per key. Verification on write: checksum validation.

## API-025 · GET /v2/customers/customers/export
**Retrieve export data for the Customers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `customers:read`, `customers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 52): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/customers/customers/export
{
  "amount": 43893,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "EXP-7700",
  "status": "pending",
  "created_at": "2026-09-19T05:39:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 79 req/min per key. Verification on write: schema validation.

## API-026 · POST /v2/webhooks/webhooks
**Create or submit a webhooks record in the Webhooks module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `webhooks:read`, `webhooks:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/webhooks/webhooks
{
  "amount": 65962,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "WEB-9979",
  "status": "succeeded",
  "created_at": "2026-09-19T02:26:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 263 req/min per key. Verification on write: format validation.

## API-027 · DELETE /v2/webhooks/webhooks/{id}/test
**Delete the referenced test record (soft-delete; retained per the data retention policy).**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `webhooks:read`, `webhooks:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `TES-3532`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
DELETE /v2/webhooks/webhooks/{id}/test
{
  "amount": 84778,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "TES-9749",
  "status": "created",
  "created_at": "2026-09-19T20:10:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 238 req/min per key. Verification on write: signature verification.

## API-028 · POST /v2/webhooks/webhooks/{id}/logs
**Create or submit a logs record in the Webhooks module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `webhooks:read`, `webhooks:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `LOG-5641`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/webhooks/webhooks/{id}/logs
{
  "amount": 88531,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "LOG-6039",
  "status": "succeeded",
  "created_at": "2026-09-19T01:19:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 205 req/min per key. Verification on write: signature verification.

## API-029 · GET /v2/webhooks/webhooks/events
**Retrieve events data for the Webhooks module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `webhooks:read`, `webhooks:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 156): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/webhooks/webhooks/events
{
  "amount": 3387,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "EVE-6960",
  "status": "active",
  "created_at": "2026-09-19T12:46:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 112 req/min per key. Verification on write: checksum validation.

## API-030 · GET /v2/webhooks/webhooks/samples
**Retrieve samply data for the Webhooks module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `webhooks:read`, `webhooks:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 90): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/webhooks/webhooks/samples
{
  "amount": 56542,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SAM-2860",
  "status": "created",
  "created_at": "2026-09-19T12:36:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 177 req/min per key. Verification on write: schema validation.

## API-031 · GET /v2/fx/fx/rates
**Retrieve raty data for the FX module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fx:read`, `fx:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 53): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fx/fx/rates
{
  "amount": 7775,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "RAT-3334",
  "status": "succeeded",
  "created_at": "2026-09-19T02:36:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 297 req/min per key. Verification on write: signature verification.

## API-032 · GET /v2/fx/fx/convert
**Retrieve convert data for the FX module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fx:read`, `fx:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 87): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fx/fx/convert
{
  "amount": 46605,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CON-5641",
  "status": "active",
  "created_at": "2026-09-19T16:10:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 87 req/min per key. Verification on write: format validation.

## API-033 · GET /v2/fx/fx/lock
**Retrieve lock data for the FX module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fx:read`, `fx:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 100): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fx/fx/lock
{
  "amount": 40533,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "LOC-3075",
  "status": "created",
  "created_at": "2026-09-19T15:20:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 215 req/min per key. Verification on write: sandbox dry-run.

## API-034 · GET /v2/fx/fx/pairs
**Retrieve pairs data for the FX module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fx:read`, `fx:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 72): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fx/fx/pairs
{
  "amount": 82309,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "PAI-3625",
  "status": "active",
  "created_at": "2026-09-19T19:25:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 276 req/min per key. Verification on write: schema validation.

## API-035 · GET /v2/fx/fx/history
**Retrieve history data for the FX module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fx:read`, `fx:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 96): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fx/fx/history
{
  "amount": 75111,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "HIS-4573",
  "status": "created",
  "created_at": "2026-09-19T12:33:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 158 req/min per key. Verification on write: signature verification.

## API-036 · POST /v2/subscriptions/subscriptions
**Create or submit a subscriptions record in the Subscriptions module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `subscriptions:read`, `subscriptions:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/subscriptions/subscriptions
{
  "amount": 20590,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SUB-5047",
  "status": "active",
  "created_at": "2026-09-19T01:56:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 275 req/min per key. Verification on write: sandbox dry-run.

## API-037 · POST /v2/subscriptions/subscriptions/plans
**Create or submit a plans record in the Subscriptions module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `subscriptions:read`, `subscriptions:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/subscriptions/subscriptions/plans
{
  "amount": 88542,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "PLA-6311",
  "status": "created",
  "created_at": "2026-09-19T12:38:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 200 req/min per key. Verification on write: sandbox dry-run.

## API-038 · POST /v2/subscriptions/subscriptions/{id}/cancel
**Create or submit a cancel record in the Subscriptions module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `subscriptions:read`, `subscriptions:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `CAN-7882`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/subscriptions/subscriptions/{id}/cancel
{
  "amount": 41397,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "CAN-5083",
  "status": "succeeded",
  "created_at": "2026-09-19T12:42:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 174 req/min per key. Verification on write: idempotency-key deduplication.

## API-039 · GET /v2/subscriptions/subscriptions/dunning
**Retrieve dunning data for the Subscriptions module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `subscriptions:read`, `subscriptions:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 95): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/subscriptions/subscriptions/dunning
{
  "amount": 4063,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "DUN-1057",
  "status": "succeeded",
  "created_at": "2026-09-19T14:15:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 255 req/min per key. Verification on write: idempotency-key deduplication.

## API-040 · GET /v2/subscriptions/subscriptions/usage
**Retrieve usage data for the Subscriptions module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `subscriptions:read`, `subscriptions:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 95): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/subscriptions/subscriptions/usage
{
  "amount": 63025,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "USA-7559",
  "status": "created",
  "created_at": "2026-09-19T02:08:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 170 req/min per key. Verification on write: signature verification.

## API-041 · POST /v2/cards/cards/tokens
**Create or submit a tokens record in the Cards module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `cards:read`, `cards:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/cards/cards/tokens
{
  "amount": 58929,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "TOK-9263",
  "status": "created",
  "created_at": "2026-09-19T01:40:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 81 req/min per key. Verification on write: sandbox dry-run.

## API-042 · POST /v2/cards/cards/{token}
**Create or submit a  record in the Cards module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `cards:read`, `cards:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `-9380`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/cards/cards/{token}
{
  "amount": 11481,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "-1889",
  "status": "succeeded",
  "created_at": "2026-09-19T20:50:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 66 req/min per key. Verification on write: checksum validation.

## API-043 · POST /v2/cards/cards/network-tokens
**Create or submit a network-tokens record in the Cards module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `cards:read`, `cards:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/cards/cards/network-tokens
{
  "amount": 26389,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "NET-3156",
  "status": "succeeded",
  "created_at": "2026-09-19T09:51:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 235 req/min per key. Verification on write: sandbox dry-run.

## API-044 · GET /v2/cards/cards/3ds/sessions
**Retrieve sessions data for the Cards module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `cards:read`, `cards:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 66): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/cards/cards/3ds/sessions
{
  "amount": 46992,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SES-5132",
  "status": "active",
  "created_at": "2026-09-19T10:57:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 130 req/min per key. Verification on write: format validation.

## API-045 · GET /v2/cards/cards/declines
**Retrieve decliny data for the Cards module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `cards:read`, `cards:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 115): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/cards/cards/declines
{
  "amount": 66826,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "DEC-8866",
  "status": "active",
  "created_at": "2026-09-19T18:16:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 189 req/min per key. Verification on write: schema validation.

## API-046 · GET /v2/transfers/transfers
**Retrieve transfers data for the Transfers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `transfers:read`, `transfers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 145): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/transfers/transfers
{
  "amount": 5827,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "TRA-4259",
  "status": "active",
  "created_at": "2026-09-19T12:10:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 299 req/min per key. Verification on write: signature verification.

## API-047 · DELETE /v2/transfers/transfers/{id}/tracking
**Delete the referenced tracking record (soft-delete; retained per the data retention policy).**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `transfers:read`, `transfers:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `TRA-6371`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
DELETE /v2/transfers/transfers/{id}/tracking
{
  "amount": 50393,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "TRA-3764",
  "status": "pending",
  "created_at": "2026-09-19T03:49:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 72 req/min per key. Verification on write: sandbox dry-run.

## API-048 · GET /v2/transfers/transfers/sepa/batches
**Retrieve batchy data for the Transfers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `transfers:read`, `transfers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 165): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/transfers/transfers/sepa/batches
{
  "amount": 73768,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "BAT-9543",
  "status": "created",
  "created_at": "2026-09-19T08:34:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 279 req/min per key. Verification on write: format validation.

## API-049 · GET /v2/transfers/transfers/ach
**Retrieve ach data for the Transfers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `transfers:read`, `transfers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 117): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/transfers/transfers/ach
{
  "amount": 50248,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "ACH-7044",
  "status": "active",
  "created_at": "2026-09-19T11:21:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 173 req/min per key. Verification on write: schema validation.

## API-050 · GET /v2/transfers/transfers/limits
**Retrieve limits data for the Transfers module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `transfers:read`, `transfers:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 62): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/transfers/transfers/limits
{
  "amount": 39847,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "LIM-9455",
  "status": "pending",
  "created_at": "2026-09-19T09:40:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 297 req/min per key. Verification on write: sandbox dry-run.

## API-051 · GET /v2/payouts/payouts
**Retrieve payouts data for the Payouts module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payouts:read`, `payouts:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 50): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payouts/payouts
{
  "amount": 5429,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "PAY-4631",
  "status": "active",
  "created_at": "2026-09-19T09:39:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 170 req/min per key. Verification on write: format validation.

## API-052 · GET /v2/payouts/payouts/batches
**Retrieve batchy data for the Payouts module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payouts:read`, `payouts:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 62): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payouts/payouts/batches
{
  "amount": 18304,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "BAT-9001",
  "status": "active",
  "created_at": "2026-09-19T19:41:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 65 req/min per key. Verification on write: checksum validation.

## API-053 · POST /v2/payouts/payouts/schedules
**Create or submit a scheduly record in the Payouts module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payouts:read`, `payouts:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/payouts/payouts/schedules
{
  "amount": 75333,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SCH-6815",
  "status": "pending",
  "created_at": "2026-09-19T03:33:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 196 req/min per key. Verification on write: schema validation.

## API-054 · GET /v2/payouts/payouts/rules
**Retrieve ruly data for the Payouts module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payouts:read`, `payouts:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 199): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/payouts/payouts/rules
{
  "amount": 40472,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "RUL-3190",
  "status": "active",
  "created_at": "2026-09-19T11:39:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 100 req/min per key. Verification on write: schema validation.

## API-055 · POST /v2/payouts/payouts/holds
**Create or submit a holds record in the Payouts module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `payouts:read`, `payouts:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/payouts/payouts/holds
{
  "amount": 32927,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "HOL-3446",
  "status": "succeeded",
  "created_at": "2026-09-19T03:04:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 97 req/min per key. Verification on write: sandbox dry-run.

## API-056 · GET /v2/tax/tax/calculate
**Retrieve calculate data for the Tax module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `tax:read`, `tax:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 152): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/tax/tax/calculate
{
  "amount": 35634,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CAL-1188",
  "status": "created",
  "created_at": "2026-09-19T20:52:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 288 req/min per key. Verification on write: signature verification.

## API-057 · GET /v2/tax/tax/ids/validate
**Retrieve validate data for the Tax module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `tax:read`, `tax:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 182): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/tax/tax/ids/validate
{
  "amount": 65599,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "VAL-5071",
  "status": "active",
  "created_at": "2026-09-19T00:02:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 196 req/min per key. Verification on write: checksum validation.

## API-058 · GET /v2/tax/tax/filings
**Retrieve filings data for the Tax module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `tax:read`, `tax:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 97): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/tax/tax/filings
{
  "amount": 32151,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "FIL-3608",
  "status": "created",
  "created_at": "2026-09-19T03:00:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 201 req/min per key. Verification on write: sandbox dry-run.

## API-059 · GET /v2/tax/tax/regimes
**Retrieve regimy data for the Tax module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `tax:read`, `tax:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 86): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/tax/tax/regimes
{
  "amount": 55156,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "REG-4268",
  "status": "succeeded",
  "created_at": "2026-09-19T19:11:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 139 req/min per key. Verification on write: checksum validation.

## API-060 · GET /v2/tax/tax/invoices
**Retrieve invoicy data for the Tax module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `tax:read`, `tax:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 62): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/tax/tax/invoices
{
  "amount": 63642,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "INV-9821",
  "status": "created",
  "created_at": "2026-09-19T12:54:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 250 req/min per key. Verification on write: format validation.

## API-061 · POST /v2/fraud/fraud/score
**Create or submit a score record in the Fraud module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fraud:read`, `fraud:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/fraud/fraud/score
{
  "amount": 86921,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SCO-8413",
  "status": "active",
  "created_at": "2026-09-19T07:06:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 119 req/min per key. Verification on write: sandbox dry-run.

## API-062 · POST /v2/fraud/fraud/rules
**Create or submit a ruly record in the Fraud module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fraud:read`, `fraud:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/fraud/fraud/rules
{
  "amount": 17156,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "RUL-6497",
  "status": "pending",
  "created_at": "2026-09-19T22:03:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 222 req/min per key. Verification on write: idempotency-key deduplication.

## API-063 · GET /v2/fraud/fraud/devices
**Retrieve devicy data for the Fraud module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fraud:read`, `fraud:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 183): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fraud/fraud/devices
{
  "amount": 35772,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "DEV-5843",
  "status": "active",
  "created_at": "2026-09-19T02:56:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 63 req/min per key. Verification on write: schema validation.

## API-064 · GET /v2/fraud/fraud/blocklist
**Retrieve blocklist data for the Fraud module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fraud:read`, `fraud:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 110): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fraud/fraud/blocklist
{
  "amount": 27578,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "BLO-3608",
  "status": "pending",
  "created_at": "2026-09-19T06:56:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 144 req/min per key. Verification on write: idempotency-key deduplication.

## API-065 · GET /v2/fraud/fraud/cases
**Retrieve casy data for the Fraud module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `fraud:read`, `fraud:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 147): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/fraud/fraud/cases
{
  "amount": 83666,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CAS-9787",
  "status": "succeeded",
  "created_at": "2026-09-19T15:53:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 238 req/min per key. Verification on write: checksum validation.

## API-066 · POST /v2/vault/vault/secrets
**Create or submit a secrets record in the Vault module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `vault:read`, `vault:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/vault/vault/secrets
{
  "amount": 58306,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "SEC-4831",
  "status": "pending",
  "created_at": "2026-09-19T06:25:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 209 req/min per key. Verification on write: checksum validation.

## API-067 · DELETE /v2/vault/vault/secrets/{id}/versions
**Delete the referenced versions record (soft-delete; retained per the data retention policy).**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `vault:read`, `vault:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `VER-3810`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
DELETE /v2/vault/vault/secrets/{id}/versions
{
  "amount": 19952,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "VER-1539",
  "status": "created",
  "created_at": "2026-09-19T03:06:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 297 req/min per key. Verification on write: schema validation.

## API-068 · GET /v2/vault/vault/keys
**Retrieve keys data for the Vault module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `vault:read`, `vault:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 86): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/vault/vault/keys
{
  "amount": 4766,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "KEY-1505",
  "status": "created",
  "created_at": "2026-09-19T04:44:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 222 req/min per key. Verification on write: checksum validation.

## API-069 · POST /v2/vault/vault/policies
**Create or submit a policiy record in the Vault module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `vault:read`, `vault:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/vault/vault/policies
{
  "amount": 7119,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "POL-2077",
  "status": "pending",
  "created_at": "2026-09-19T06:52:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 288 req/min per key. Verification on write: sandbox dry-run.

## API-070 · POST /v2/vault/vault/audit
**Create or submit a audit record in the Vault module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `vault:read`, `vault:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/vault/vault/audit
{
  "amount": 51311,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "AUD-2754",
  "status": "active",
  "created_at": "2026-09-19T06:13:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 68 req/min per key. Verification on write: checksum validation.

## API-071 · POST /v2/ledger/ledger/entries
**Create or submit a entriy record in the Ledger module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `ledger:read`, `ledger:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/ledger/ledger/entries
{
  "amount": 83776,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "ENT-5708",
  "status": "succeeded",
  "created_at": "2026-09-19T03:08:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 262 req/min per key. Verification on write: sandbox dry-run.

## API-072 · GET /v2/ledger/ledger/accounts
**Retrieve accounts data for the Ledger module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `ledger:read`, `ledger:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 125): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/ledger/ledger/accounts
{
  "amount": 42830,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "ACC-6513",
  "status": "succeeded",
  "created_at": "2026-09-19T08:01:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 125 req/min per key. Verification on write: signature verification.

## API-073 · POST /v2/ledger/ledger/balances
**Create or submit a balancy record in the Ledger module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `ledger:read`, `ledger:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/ledger/ledger/balances
{
  "amount": 49237,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "BAL-6256",
  "status": "succeeded",
  "created_at": "2026-09-19T09:39:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 67 req/min per key. Verification on write: format validation.

## API-074 · POST /v2/ledger/ledger/journals
**Create or submit a journals record in the Ledger module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `ledger:read`, `ledger:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/ledger/ledger/journals
{
  "amount": 58206,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "JOU-9497",
  "status": "created",
  "created_at": "2026-09-19T11:30:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 72 req/min per key. Verification on write: idempotency-key deduplication.

## API-075 · GET /v2/ledger/ledger/close
**Retrieve close data for the Ledger module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `ledger:read`, `ledger:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 73): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/ledger/ledger/close
{
  "amount": 76306,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CLO-5704",
  "status": "active",
  "created_at": "2026-09-19T13:00:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 111 req/min per key. Verification on write: signature verification.

## API-076 · POST /v2/notifications/notifications/email
**Create or submit a email record in the Notifications module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `notifications:read`, `notifications:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/notifications/notifications/email
{
  "amount": 1571,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "EMA-6698",
  "status": "succeeded",
  "created_at": "2026-09-19T03:31:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 263 req/min per key. Verification on write: schema validation.

## API-077 · GET /v2/notifications/notifications/sms
**Retrieve sms data for the Notifications module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `notifications:read`, `notifications:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 138): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/notifications/notifications/sms
{
  "amount": 68520,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SMS-5269",
  "status": "active",
  "created_at": "2026-09-19T09:52:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 300 req/min per key. Verification on write: sandbox dry-run.

## API-078 · GET /v2/notifications/notifications/push
**Retrieve push data for the Notifications module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `notifications:read`, `notifications:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 177): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/notifications/notifications/push
{
  "amount": 22730,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "PUS-2800",
  "status": "created",
  "created_at": "2026-09-19T15:50:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 203 req/min per key. Verification on write: checksum validation.

## API-079 · GET /v2/notifications/notifications/templates
**Retrieve templaty data for the Notifications module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `notifications:read`, `notifications:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 141): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/notifications/notifications/templates
{
  "amount": 13471,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "TEM-7574",
  "status": "succeeded",
  "created_at": "2026-09-19T23:05:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 287 req/min per key. Verification on write: sandbox dry-run.

## API-080 · POST /v2/notifications/notifications/logs
**Create or submit a logs record in the Notifications module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `notifications:read`, `notifications:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/notifications/notifications/logs
{
  "amount": 49752,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "LOG-4377",
  "status": "pending",
  "created_at": "2026-09-19T08:27:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 188 req/min per key. Verification on write: schema validation.

## API-081 · GET /v2/identity/identity/verify
**Retrieve verify data for the Identity module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `identity:read`, `identity:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 109): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/identity/identity/verify
{
  "amount": 61412,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "VER-3078",
  "status": "created",
  "created_at": "2026-09-19T11:37:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 193 req/min per key. Verification on write: schema validation.

## API-082 · GET /v2/identity/identity/documents
**Retrieve documents data for the Identity module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `identity:read`, `identity:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 191): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/identity/identity/documents
{
  "amount": 43380,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "DOC-3777",
  "status": "succeeded",
  "created_at": "2026-09-19T14:44:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 208 req/min per key. Verification on write: schema validation.

## API-083 · GET /v2/identity/identity/biometrics
**Retrieve biometrics data for the Identity module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `identity:read`, `identity:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 135): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/identity/identity/biometrics
{
  "amount": 61557,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "BIO-4898",
  "status": "active",
  "created_at": "2026-09-19T08:19:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 271 req/min per key. Verification on write: idempotency-key deduplication.

## API-084 · GET /v2/identity/identity/kyc
**Retrieve kyc data for the Identity module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `identity:read`, `identity:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 89): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/identity/identity/kyc
{
  "amount": 33450,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "KYC-6350",
  "status": "pending",
  "created_at": "2026-09-19T05:15:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 108 req/min per key. Verification on write: signature verification.

## API-085 · POST /v2/identity/identity/rescreen
**Create or submit a rescreen record in the Identity module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `identity:read`, `identity:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/identity/identity/rescreen
{
  "amount": 22574,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "RES-2665",
  "status": "active",
  "created_at": "2026-09-19T12:09:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 263 req/min per key. Verification on write: signature verification.

## API-086 · GET /v2/marketplace/marketplace/sellers
**Retrieve sellers data for the Marketplace module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `marketplace:read`, `marketplace:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 161): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/marketplace/marketplace/sellers
{
  "amount": 36890,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SEL-4214",
  "status": "created",
  "created_at": "2026-09-19T20:58:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 131 req/min per key. Verification on write: schema validation.

## API-087 · GET /v2/marketplace/marketplace/settlements
**Retrieve settlements data for the Marketplace module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `marketplace:read`, `marketplace:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 168): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/marketplace/marketplace/settlements
{
  "amount": 5447,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SET-1206",
  "status": "succeeded",
  "created_at": "2026-09-19T13:44:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 188 req/min per key. Verification on write: sandbox dry-run.

## API-088 · GET /v2/marketplace/marketplace/fees
**Retrieve fey data for the Marketplace module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `marketplace:read`, `marketplace:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 168): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/marketplace/marketplace/fees
{
  "amount": 3898,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "FEE-3323",
  "status": "pending",
  "created_at": "2026-09-19T19:47:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 61 req/min per key. Verification on write: sandbox dry-run.

## API-089 · GET /v2/marketplace/marketplace/listings
**Retrieve listings data for the Marketplace module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `marketplace:read`, `marketplace:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 160): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/marketplace/marketplace/listings
{
  "amount": 76232,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "LIS-7900",
  "status": "active",
  "created_at": "2026-09-19T21:46:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 285 req/min per key. Verification on write: sandbox dry-run.

## API-090 · GET /v2/marketplace/marketplace/claims
**Retrieve claims data for the Marketplace module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `marketplace:read`, `marketplace:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 96): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/marketplace/marketplace/claims
{
  "amount": 85087,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "CLA-3035",
  "status": "succeeded",
  "created_at": "2026-09-19T13:20:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 220 req/min per key. Verification on write: sandbox dry-run.

## API-091 · POST /v2/reconciliation/reconciliation/runs
**Create or submit a runs record in the Reconciliation module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reconciliation:read`, `reconciliation:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/reconciliation/reconciliation/runs
{
  "amount": 55995,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "RUN-4971",
  "status": "succeeded",
  "created_at": "2026-09-19T22:45:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 100 req/min per key. Verification on write: signature verification.

## API-092 · GET /v2/reconciliation/reconciliation/statements
**Retrieve statements data for the Reconciliation module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reconciliation:read`, `reconciliation:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 173): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reconciliation/reconciliation/statements
{
  "amount": 60663,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "STA-1322",
  "status": "succeeded",
  "created_at": "2026-09-19T16:43:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 298 req/min per key. Verification on write: schema validation.

## API-093 · GET /v2/reconciliation/reconciliation/rules
**Retrieve ruly data for the Reconciliation module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reconciliation:read`, `reconciliation:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 52): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reconciliation/reconciliation/rules
{
  "amount": 51948,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "RUL-9025",
  "status": "created",
  "created_at": "2026-09-19T01:16:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 115 req/min per key. Verification on write: schema validation.

## API-094 · GET /v2/reconciliation/reconciliation/mismatches
**Retrieve mismatchy data for the Reconciliation module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reconciliation:read`, `reconciliation:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 182): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/reconciliation/reconciliation/mismatches
{
  "amount": 46640,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "MIS-2656",
  "status": "succeeded",
  "created_at": "2026-09-19T17:13:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 181 req/min per key. Verification on write: idempotency-key deduplication.

## API-095 · POST /v2/reconciliation/reconciliation/audit
**Create or submit a audit record in the Reconciliation module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `reconciliation:read`, `reconciliation:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/reconciliation/reconciliation/audit
{
  "amount": 84789,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "AUD-7060",
  "status": "pending",
  "created_at": "2026-09-19T13:47:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 113 req/min per key. Verification on write: sandbox dry-run.

## API-096 · GET /v2/compliance/compliance/sanctions
**Retrieve sanctions data for the Compliance module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `compliance:read`, `compliance:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 150): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/compliance/compliance/sanctions
{
  "amount": 68343,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SAN-3005",
  "status": "pending",
  "created_at": "2026-09-19T20:03:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 130 req/min per key. Verification on write: format validation.

## API-097 · GET /v2/compliance/compliance/aml
**Retrieve aml data for the Compliance module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `compliance:read`, `compliance:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 65): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/compliance/compliance/aml
{
  "amount": 2744,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "AML-2231",
  "status": "succeeded",
  "created_at": "2026-09-19T13:40:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 232 req/min per key. Verification on write: signature verification.

## API-098 · GET /v2/compliance/compliance/filings
**Retrieve filings data for the Compliance module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `compliance:read`, `compliance:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 77): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/compliance/compliance/filings
{
  "amount": 30416,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "FIL-5972",
  "status": "succeeded",
  "created_at": "2026-09-19T16:14:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 178 req/min per key. Verification on write: schema validation.

## API-099 · GET /v2/compliance/compliance/audit
**Retrieve audit data for the Compliance module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `compliance:read`, `compliance:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 83): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/compliance/compliance/audit
{
  "amount": 10030,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "AUD-4164",
  "status": "succeeded",
  "created_at": "2026-09-19T20:35:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 117 req/min per key. Verification on write: schema validation.

## API-100 · GET /v2/compliance/compliance/reports
**Retrieve reports data for the Compliance module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `compliance:read`, `compliance:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 155): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/compliance/compliance/reports
{
  "amount": 62354,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "REP-5822",
  "status": "active",
  "created_at": "2026-09-19T15:22:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 128 req/min per key. Verification on write: sandbox dry-run.

## API-101 · GET /v2/support/support/tickets
**Retrieve tickets data for the Support module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `support:read`, `support:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 114): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/support/support/tickets
{
  "amount": 56850,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "TIC-4045",
  "status": "succeeded",
  "created_at": "2026-09-19T00:51:00Z"
}
```

**Errors:** 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict. Rate limit: 264 req/min per key. Verification on write: signature verification.

## API-102 · POST /v2/support/support/tickets/{id}
**Create or submit a  record in the Support module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `support:read`, `support:write`.

**Parameters**
- `id` (string, path, required): resource ID (e.g. `-5013`)
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/support/support/tickets/{id}
{
  "amount": 86773,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "-5945",
  "status": "pending",
  "created_at": "2026-09-19T15:31:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 219 req/min per key. Verification on write: sandbox dry-run.

## API-103 · POST /v2/support/support/feedback
**Create or submit a feedback record in the Support module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `support:read`, `support:write`.

**Parameters**
- `amount` (number, body, conditional): monetary value in minor units where the resource is financial
- `idempotency_key` (string, header, recommended): makes retries safe
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
POST /v2/support/support/feedback
{
  "amount": 87411,
  "currency": "USD",
  "metadata": {"source": "agent"}
}
```

**Example response (200/201)**
```
{
  "id": "FEE-6938",
  "status": "active",
  "created_at": "2026-09-19T09:54:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 74 req/min per key. Verification on write: checksum validation.

## API-104 · GET /v2/support/support/slas
**Retrieve slas data for the Support module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `support:read`, `support:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 85): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/support/support/slas
{
  "amount": 70553,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "SLA-6654",
  "status": "created",
  "created_at": "2026-09-19T21:00:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found, 409 idempotency_conflict, 422 validation_failed, 429 rate_limited, 500 internal_error. Rate limit: 78 req/min per key. Verification on write: sandbox dry-run.

## API-105 · GET /v2/support/support/agents
**Retrieve agents data for the Support module.**

**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `support:read`, `support:write`.

**Parameters**
- `limit` (integer, query, optional, default 20, max 114): page size
- `offset` (integer, query, optional, default 0): pagination offset
- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data

**Example request**
```
GET /v2/support/support/agents
{
  "amount": 80718,
  "currency": "USD",
}
```

**Example response (200/201)**
```
{
  "id": "AGE-2663",
  "status": "active",
  "created_at": "2026-09-19T07:11:00Z"
}
```

**Errors:** 400 invalid_request, 401 unauthorized, 403 insufficient_scope, 404 not_found. Rate limit: 148 req/min per key. Verification on write: schema validation.

## API-106 · GET /v2/health
Liveness probe. No auth required. Returns service status, version and region.

Rate limit: 113 req/min. Verification: format validation.

## API-107 · POST /v2/oauth/token
Exchange a client credential grant for an access token (20 min TTL).

Rate limit: 262 req/min. Verification: idempotency-key deduplication.

## API-108 · GET /v2/sandbox/state
Snapshot of the current sandbox fixtures (transactions, customers, invoices).

Rate limit: 102 req/min. Verification: idempotency-key deduplication.

## API-109 · POST /v2/sandbox/reset
Reset sandbox state to the canonical fixture set. Idempotent.

Rate limit: 288 req/min. Verification: sandbox dry-run.

## API-110 · GET /v2/accounts/me
The authenticated business account: id, scopes, rate limits, plan.

Rate limit: 215 req/min. Verification: checksum validation.

## API-111 · GET /v2/audit/recent
The 100 most recent authenticated actions with actor, scope and IP.

Rate limit: 231 req/min. Verification: idempotency-key deduplication.

## API-112 · GET /v2/feature-flags
Feature flags enabled for the account (beta opt-ins).

Rate limit: 261 req/min. Verification: sandbox dry-run.

## API-113 · POST /v2/batches
Generic bulk-write batch: up to 1000 sub-operations, applied atomically.

Rate limit: 274 req/min. Verification: signature verification.

## API-114 · GET /v2/batches/{id}
Batch status and per-operation results.

Rate limit: 110 req/min. Verification: format validation.

## API-115 · DELETE /v2/batches/{id}
Cancel a queued batch before execution.

Rate limit: 237 req/min. Verification: schema validation.
