### Bug fix

**When this matches:** a reported defect. Something behaves wrongly today and
the work is to reproduce it, find why, and fix it.

**Decision axes the frontier must cover**

- The exact reproduction: input, environment, expected versus observed.
- Blast radius: who is affected, since when, how often.
- Root cause versus symptom — and whether the fix belongs at the reported site
  or upstream of it.
- Whether related call sites carry the same defect.
- What regression test proves the fix and would have caught the bug.
- Urgency: hotfix, backport, or next release.

**Facts to dispatch, never ask**

- `git log` over the implicated files, and the last change that touched them.
- Existing test coverage over that surface.
- Whether a similar bug was reported or fixed before.

**Spec sections this task type requires**

- **Reproduction** — the steps, verbatim and runnable.
- **Root cause** — the mechanism, not the symptom.
- **Fix** — what changes and why there rather than elsewhere.
- **Regression test** — the test that fails before and passes after.

Omitting a required section needs its reason written into the spec at that point.

**Red flags**

| Thought | Reality |
|---|---|
| "I can see the bug, no need to reproduce it" | Without a reproduction you cannot tell a fix from a coincidence. |
| "Ask the user for the stack trace" | Ask for what only they have. Anything in the repo or the logs is yours to find. |
| "The symptom is gone, so it is fixed" | Name the mechanism. A gone symptom with an unknown cause comes back. |
| "A test would slow this down" | The regression test is the deliverable that stops the second report. |
