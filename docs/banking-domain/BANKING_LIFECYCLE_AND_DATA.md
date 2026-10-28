# Banking Lifecycle and Data Concepts

## 1. Customer and account lifecycle
A simplified customer/account lifecycle may include:
1. Customer onboarding and identity verification.
2. Customer due diligence and risk classification according to applicable requirements.
3. Account opening and product setup.
4. Ongoing account maintenance and monitoring.
5. Transactions, service requests, reviews, and disputes.
6. Account closure or relationship termination where applicable.

The exact steps, evidence requirements, retention periods, and approvals depend on the institution, product, and law. Do not encode a universal compliance process without source verification.

## 2. Payment and ledger lifecycle are different
A payment instruction can be created, validated, authorized, routed, accepted or rejected by a network, posted to one or more systems, settled, reversed, disputed, or reconciled. The exact states and order differ by rail and institution.

A bank ledger records accounting entries. For a balanced double-entry accounting system, each journal entry balances according to the ledger's currency/accounting rules. A payment message or network status is not itself a substitute for ledger entries.

## 3. Status modeling
Prefer explicit statuses and source-specific events, for example:
- `initiated`
- `pending`
- `accepted`
- `posted`
- `settled`
- `failed`
- `reversed`
- `returned`
- `disputed`
These are illustrative normalized labels, not a universal payment-state enum. Map actual source states carefully and preserve the original source status.

Do not assume `accepted == settled`, `posted == irrevocable`, or `failed == no funds movement` without understanding the source system and payment rail.

## 4. Timestamps
Store UTC timestamps and retain what each timestamp represents:
- `initiated_at`: instruction created.
- `authorized_at`: authorization event.
- `network_received_at`: network or switch receipt.
- `posted_at`: ledger posting.
- `settled_at`: settlement event, if provided by an authoritative source.
- `observed_at`: when the system ingested or observed the record.
These are examples. Do not invent missing timestamps. Distinguish event time from ingestion time and use explicit source timezone information when available.

## 5. Money and currency
- Use decimal-safe numeric types for money, not binary floating-point.
- Store currency explicitly, usually as a currency code.
- Do not add amounts in different currencies without a documented FX rate, source, rate timestamp, and conversion policy.
- Fees, holds, reversals, partial returns, and other transfers may affect balance calculations.
- The difference between two transfer amounts is not proof of a current account balance.
- A transaction amount is not necessarily the amount of loss or amount finally received by a beneficiary.

## 6. Reconciliation
Reconciliation compares records from two or more systems or parties to identify matched items, unmatched items, duplicates, timing differences, amount differences, and status differences. Examples include bank ledger versus payment network records or statement entries versus internal records.

For the project, reconciliation can be a future extension. Do not imply a transaction is missing or fraudulent merely because records are not yet matched; it may be a timing or data-quality issue.

## 7. Identifiers and linkage
A customer may have multiple accounts; a beneficiary may be represented as an account, VPA, card token, wallet, merchant, or external identifier depending on the rail. Identifier linkage may be uncertain. A shared device, phone, IP, address, or beneficiary does not by itself prove common ownership or collusion.

Represent relationship type and provenance. Avoid collapsing distinct identifiers into one entity unless an explicit linkage rule and confidence/provenance are recorded.
