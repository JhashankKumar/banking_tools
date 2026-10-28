# Security Policy

## Supported versions

The project is pre-release. Only the `main` branch receives security fixes.

## Reporting a vulnerability

Please report vulnerabilities privately using GitHub's **[private vulnerability reporting](../../security/advisories/new)** (Security tab → "Report a vulnerability"). Do not open a public issue.

Include:

- a description of the issue and its impact,
- steps to reproduce using synthetic data,
- affected files, endpoints, or versions.

Never include real customer data, real credentials, or secrets in a report.

## Scope

OpenFraud Investigator is a demonstration application that uses synthetic data only. Of particular interest:

- authorization bypass (accessing cases, records, or actions outside a role's permissions),
- prompt injection that changes AI tool use, permissions, or evidence,
- AI answers citing evidence that does not exist or was not authorized,
- secret or sensitive-data exposure in logs, responses, or client code.

The project makes no claim of production readiness or regulatory compliance.
