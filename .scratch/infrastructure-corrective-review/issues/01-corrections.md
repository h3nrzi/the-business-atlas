# Correct infrastructure integrity and restricted-source tracking
Status: ready-for-agent

Spec: ../spec.md

Implement the user's corrective scope, validate it, review standards and spec,
prepare feature-by-feature evaluation, then commit and push main normally.

## Comments

2026-10-18: fetched both remote branches; main clean and canonical. Public GitHub
API confirmed raw CSV availability. Only meaningful branch code delta is generated
output normalization; preserve owner tracker files and avoid redundant merge.

2026-10-18: implementation complete in fb6c7e58df79f0d399a2b2078e74ab351c7da17e.
33 tests and both check modes pass; Standards 0 findings, Spec 0 findings.
Hands-on guide prepared at ../acceptance/01-corrections/guide.md; exact CLI
scenarios preflighted in a disposable synthetic sandbox. Human results not_run.
Final documentation/evaluation artifacts are recorded separately; triage status
does not represent chapter publication or human acceptance.
