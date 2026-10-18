# OpenFraud Investigator — Knowledge Base

This folder captures the project decisions and development rules agreed so far. Use it as the source of truth when asking Claude or another coding agent to implement the project.

## Files

- `PROJECT_BRIEF.md` — problem, scope, product goals, and non-goals.
- `TECH_STACK.md` — recommended technologies and rationale, including OpenRouter as the initial LLM gateway.
- `ENGINEERING_PRINCIPLES.md` — KISS, DRY, YAGNI, SOLID, cohesion, coupling, code flow, and practical rules.
- `ARCHITECTURE_AND_FOLDERS.md` — proposed modular monolith and repository layout.
- `DOMAIN_MODEL_AND_APIS.md` — core entities, endpoints, and transaction path semantics.
- `AI_AGENT_AND_SECURITY.md` — controlled tool use, evidence grounding, threat model, and authorization rules.
- `TESTING_AND_EVALUATION.md` — testing strategy, synthetic scenarios, and metrics.
- `IMPLEMENTATION_PLAN.md` — incremental implementation milestones.
- `CLAUDE_MASTER_PROMPT.md` — copy this prompt into Claude Code to start development.
- `../banking-domain/` — banking concepts, payment semantics, fraud investigation workflow, India regulatory context, synthetic casebook, AI domain guardrails, and official source register.

## How to use

1. Create a GitHub repository named `openfraud-investigator`.
2. These files live in `docs/project/` and `docs/banking-domain/`; accepted decisions are in `docs/decisions/`. Provide them to Claude as project context.
3. Open `CLAUDE_MASTER_PROMPT.md`, copy its contents into Claude Code, and ask Claude to begin with Milestone 0 and then implement one milestone at a time.
4. Ask Claude to inspect the existing repository before editing files. It must not overwrite existing work without explaining the change.
5. Review all generated code, run the tests, and inspect security-sensitive logic yourself.

## Source-of-truth rule

When implementation choices are unclear, prefer the simplest design that meets the documented requirements. Record material architecture decisions in `docs/decisions/` as short Architecture Decision Records (ADRs). Do not add infrastructure or dependencies without a concrete requirement.
