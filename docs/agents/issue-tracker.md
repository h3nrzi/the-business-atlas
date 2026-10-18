# Issue tracker: Local Markdown

Issues and specs live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`.
- Spec: `.scratch/<feature-slug>/spec.md`.
- Implementation tickets: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`,
  numbered from `01`, with one file per ticket.
- Record triage state in a `Status:` line near the top of each ticket.
  Use the strings in `triage-labels.md`.
- Append comments under a `## Comments` heading.

## When a skill says "publish to the issue tracker"

Write the spec or ticket at the corresponding path above.
Create directories as needed.

## When a skill says "fetch the relevant ticket"

Read the referenced file. Resolve ticket numbers within the feature directory.

## Wayfinding operations

Used by `/wayfinder`:

- Map: `.scratch/<effort>/map.md`, containing Notes, Decisions-so-far,
  and Fog.
- Child ticket: `.scratch/<effort>/issues/<NN>-<slug>.md`.
  Record its type in `Type:`: research, prototype, grilling, or task.
- Blocking: list prerequisite ticket numbers in `Blocked by: NN, NN`.
  A ticket is unblocked when every prerequisite is resolved.
- Frontier: select the first open, unblocked, unclaimed ticket by number.
- Claim: set `Status: claimed` and save before starting work.
- Resolve: append the answer under `## Answer`, set `Status: resolved`,
  and append a summary and relative link to Decisions-so-far in the map.

Wayfinding uses `claimed` and `resolved` as execution statuses;
triage uses the role strings in `triage-labels.md`.
