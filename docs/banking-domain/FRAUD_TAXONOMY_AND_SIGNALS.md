# Fraud Taxonomy and Investigative Signals

This is an illustrative taxonomy for synthetic scenarios, not an exhaustive legal classification or a universal bank taxonomy.

## 1. Fraud-related scenario families
- Social engineering / authorized push payment scams: a payer is deceived into authorizing a payment. Whether the payment is classified as unauthorized or treated under a particular reimbursement framework depends on the facts and applicable rules.
- Account takeover: an attacker gains access to an account or credentials and initiates activity.
- Card-not-present misuse: payment credentials are used remotely without valid authorization.
- Mule-account activity: an account may be used to receive, move, or withdraw proceeds associated with wrongdoing. Indicators can be ambiguous and require context.
- Rapid pass-through movement: funds move onward soon after receipt.
- Multi-hop transfer network: funds move through multiple entities or accounts.
- Circular flow: funds return to a prior node through one or more transactions.
- Duplicate or manipulated payment instructions.
- Beneficiary change followed by a high-risk payment.
- Unusual account behavior relative to a documented baseline.
- Internal/process fraud scenarios: suspicious employee access or unauthorized changes, represented only in synthetic audit data.
- Loan/credit fraud: suspicious documents, misrepresentation, or misuse of lending processes. This is a distinct domain and is not the MVP's main focus.

## 2. Common signal families
- Velocity: number or total value of transactions within a time window.
- Deviation from baseline: amount, frequency, geography, channel, or counterparty differs from an established and valid baseline.
- Rapid onward transfer: recipient sends funds onward soon after receipt.
- Network structure: repeated shared counterparties, unusually dense links, short paths between alert entities, or circular patterns.
- Account lifecycle context: recent account opening or recent change in account details, if reliably available.
- External signal: a validated external warning or registry match, with source, timestamp, and matching method.
- Data inconsistency: conflicting status, duplicate IDs, missing records, or time inconsistencies.
- Historical context: prior alerts/cases, preserving their actual outcomes and not treating an old alert as proof.

Signals are not proof. A high transaction amount may be legitimate; a new account may be normal; shared beneficiaries may reflect ordinary business or household relationships.

## 3. Explainable rule design
Every rule should define:
- stable rule ID and version
- plain-language description
- exact condition and time window
- required fields and data-quality preconditions
- severity rationale, if used
- false-positive caveats
- evidence record IDs
- test cases for positive and negative examples

Illustrative rule:
`RAPID_ONWARD_TRANSFER`: flag for analyst review when an entity receives a completed transfer and sends a separate completed transfer within a configured interval, subject to configured amount/relationship thresholds.
This is only a heuristic. It should not automatically label an entity as a mule or the transaction as fraud.

## 4. Avoid bad shortcuts
- Do not hardcode “large transaction” without considering currency, customer baseline, product, and context.
- Do not use a single threshold as universal truth.
- Do not label an account fraudulent because it appears in a graph path.
- Do not assume a shared identifier proves common ownership.
- Do not treat a model's risk score as a calibrated probability unless calibration was evaluated.
- Do not claim a synthetic ML score generalizes to real bank data.

## 5. Evaluation
Evaluate rule and model behavior on positive and benign-but-unusual scenarios. Track precision, recall, false-positive rate, and alert volume. If labels are imbalanced, report PR-AUC and class counts. Split by scenario families or time to avoid leakage between related transactions.
