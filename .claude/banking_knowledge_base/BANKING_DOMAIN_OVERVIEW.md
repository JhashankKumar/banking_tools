# Banking Domain Overview for OpenFraud Investigator

## 1. What a bank does
A bank accepts deposits, maintains customer accounts and ledgers, provides payment services, extends credit, performs customer due diligence, monitors risks, and maintains records for operations, controls, and regulatory reporting. The exact products, workflows, systems, and responsibilities vary by institution and jurisdiction.

## 2. Core concepts
- Customer: person or organization with a relationship to a bank.
- Customer identifier: bank-specific key used to link a customer to records. A CIF/customer ID is not universally standardized across all banks.
- Account: a product-level relationship with a unique account identifier, status, currency, and ownership/mandate attributes.
- Ledger: the authoritative accounting record of debits, credits, and balances under a defined accounting model.
- Available balance: amount currently available for use under the bank's rules; it may differ from ledger balance because of holds, uncleared items, limits, liens, or pending authorizations.
- Transaction: a business event or instruction to move value. A transaction may have multiple lifecycle events and statuses.
- Payment rail: a scheme/network and set of rules for moving payment instructions or funds, such as UPI, IMPS, NEFT, RTGS, cards, ACH, or SWIFT-related cross-border messaging. These are not interchangeable and differ by jurisdiction.
- Beneficiary/payee: intended recipient of a payment.
- Remitter/payer: party initiating or funding a payment.
- Alert: a signal raised by a rule, model, report, or external source.
- Case: a structured work item to review an alert or suspected incident.
- Evidence: a source record or reproducible derived result that supports or contradicts a claim.
- Audit trail: time-ordered records of access and actions, with actor, resource, result, and trace identifier.

## 3. Banking data is not a single universal truth
Operational systems may hold different views: payment initiation, switch/network status, core banking posting, ledger entries, dispute records, and settlement/reconciliation records. A case investigator should know which source produced a field and what that field means.

Do not merge these statuses into one vague `success` value. Preserve source, event type, status, timestamp type, and trace/reference IDs.

## 4. Common account/product examples
- Savings account: typically designed for personal deposits and payments, subject to product rules.
- Current account: often used by businesses and organizations for frequent transactions.
- Term/fixed deposit: funds placed for a defined term or under a defined deposit contract.
- Loan/credit account: records credit facility, drawdowns, repayments, interest, fees, and outstanding amounts.
- Card account: records card-related authorizations, clearing, settlement, reversals, disputes, and related account postings.
Product terms and legal treatment vary. The MVP need not implement all these products.

## 5. Common operational roles
- Operations analyst: investigates processing exceptions, failed payments, reconciliation breaks, and service issues.
- Fraud analyst: reviews suspicious activity, gathers evidence, and recommends or initiates actions permitted by policy.
- AML/compliance analyst: reviews potential money-laundering or sanctions-related alerts under applicable laws and policy.
- Supervisor: reviews escalations, decisions, or case quality.
- Auditor: reviews records and controls within authorized scope.
These roles are examples, not universal job definitions.

## 6. How this project uses banking concepts
OpenFraud Investigator focuses on a synthetic fraud case, transaction records, connected-entity analysis, evidence, and an AI-assisted narrative. It is not a core banking system, ledger, payment processor, sanctions screening engine, or regulatory reporting product.
