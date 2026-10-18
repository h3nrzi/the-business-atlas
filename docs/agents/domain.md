# Domain docs

## Layout and reading rules

This repo uses a single-context layout:

- `GLOSSARY.md` at the repo root defines domain terminology.
- `docs/adr/` contains architecture decision records.

Before exploring the codebase, read the glossary and ADRs relevant
to the area being worked on.

If these files are absent, proceed silently. The `/domain-modeling`
skill creates them lazily as terms and decisions are resolved.

## Vocabulary

Use the glossary's terms when naming domain concepts in issues,
proposals, hypotheses, and tests.

If a needed concept is missing, reconsider the terminology or note
the gap for `/domain-modeling`.

## Decision conflicts

Explicitly identify proposals that contradict an existing ADR.
Reference the ADR and explain why the decision should be reconsidered.
