# Mock Fallback Plan — Reference Materials

⚠️ **Sealed until needed.** Per Rule 4 of the workshop playbook: if a sub-team is not done by
its checkpoint time, the downstream sub-team takes the corresponding reference output below and
continues, rather than waiting idle. Hand these out only at the checkpoint moment — not before,
or teams will skip their own design work.

This copy lives only in the local working directory on `main` (untracked, not committed or
pushed) — kept here for convenience while testing the repo setup. It is **not sealed**: anyone
with a copy of this checkout can read it. Decide how to actually seal it (remove before the
real workshop, or move it somewhere access-controlled) before running the session for real.

One subfolder per language track — pick whichever a given pod is building against:

- [Node/](Node/) — reference outputs against the Node/Express implementation
- [java/](java/) — reference outputs against the Java implementation
- [python/](python/) — reference outputs against the Python implementation

Each subfolder has the same three files:

| File | Hand to... | If... |
|---|---|---|
| `4.1-requirement-agent-output.md` | Implementation sub-team | Requirement sub-team isn't done by Checkpoint 1 |
| `4.2-implementation-agent-diff.md` | Testing sub-team | Implementation sub-team isn't done by Checkpoint 2 |
| `4.3-testing-agent-output.md` | Mentors (answer key) | Testing sub-team needs a reference at Checkpoint 3 |
