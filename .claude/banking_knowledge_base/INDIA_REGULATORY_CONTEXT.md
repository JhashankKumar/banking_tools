# India Regulatory Context — Fraud Investigation

## Purpose and disclaimer
This file gives a high-level starting point for an India-oriented demo. It is not legal advice and must not be treated as a complete or current compliance checklist. Regulatory obligations depend on entity type, product, facts, applicable law, and current amendments. Verify the current official text before encoding requirements.

## 1. RBI Fraud Risk Management Directions, 2024
RBI issued revised fraud risk management directions on 15 July 2024 for different categories of regulated entities, including commercial banks and All India Financial Institutions, cooperative banks, and applicable NBFCs. Separate directions have different scopes and applicability.

For commercial banks and AIFIs, the 2024 directions cover governance, Early Warning Signals (EWS), Red Flagging of Accounts (RFA), investigation, reporting to law enforcement and RBI, Central Fraud Registry, and reporting/closure matters. They emphasize early detection, timely reporting, oversight, and internal controls. Consult the exact direction applicable to the institution and account type.

A Red Flagged Account is not the same as a final fraud classification. The direction describes red-flagging as a trigger for deeper investigation when EWS indicators create suspicion. Do not model an alert or RFA status as a judicial finding or proof of guilt.

## 2. Natural justice and fair process
RBI's 15 July 2024 press release notes that the revised directions address principles of natural justice before classifying persons/entities as fraud, taking account of the Supreme Court judgment referenced in the release. The project should therefore avoid automated final adverse classifications. It should present evidence, limitations, and a review workflow, not declare a real person or entity fraudulent.

## 3. I4C Suspect Registry and mule-account context
A Ministry of Home Affairs parliamentary response dated 17 March 2026 states that the I4C Suspect Registry was launched on 10 September 2024 with banks/financial institutions; as of 31 January 2026, it reported 27.37 lakh Layer 1 mule accounts shared with participating entities and declined transactions worth more than ₹9,518 crore.

These are reported registry/activity figures, not proof that every identifier/account was adjudicated as fraudulent or that all declined transaction value equals realized loss prevented. If quoted publicly, preserve the date, wording, and context from the official response.

## 4. RBI Annual Report 2024–25 fraud statistics
RBI's Annual Report 2024–25 reports that card/internet frauds contributed the largest number of frauds reported in the stated category breakdown: 13,516 cases involving ₹520 crore in 2024–25. The same table shows advances/loan portfolio frauds dominating by amount involved. RBI notes that amounts involved are not necessarily amounts diverted, and reporting/classification figures can be affected by prior-year cases and classification changes.

Do not describe “amount involved” as realized loss without a supporting source. Always state the report period and category.

## 5. What this project should and should not claim
Appropriate:
- “The app demonstrates evidence assembly and graph-based exploration using synthetic records.”
- “The RBI directions provide relevant context for early-warning and investigation workflows.”
- “A signal should trigger review rather than automatically prove fraud.”

Inappropriate without further evidence:
- “This app is RBI compliant/certified.”
- “The RBI mandates this exact software architecture.”
- “All Indian banks use the same investigation workflow.”
- “A suspect-registry match proves guilt.”
- “A synthetic benchmark proves real-world fraud prevention.”

## 6. Regulatory source verification
Before implementing a regulatory requirement:
1. Identify the regulated entity type and product.
2. Open the current official RBI/MHA/NPCI source.
3. Record the publication/effective/update date and relevant section.
4. Distinguish binding requirement from guidance, press-release summary, or general practice.
5. Add the source URL and a short note to `SOURCE_REGISTER.md`.
6. Add a test or acceptance criterion only after the requirement is understood.
