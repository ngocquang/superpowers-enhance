### Refactoring

**When this matches:** a change to structure or shape that must leave behavior
identical — rename, extract, inline, dedupe, move, split.

**Decision axes the frontier must cover**

- The behavior contract being held invariant, stated precisely enough to check.
- The full call-site inventory, including tests, docs, and dynamic references.
- One sweep or incremental steps, and where the intermediate states are safe.
- What evidence proves behavior did not change.
- Public API breakage, and whether consumers outside this repo are affected.
- What is deliberately left alone.

**Facts to dispatch, never ask**

- Every call site, including string-based and reflective references.
- Existing test coverage over the surface being moved.
- Whether the symbol is exported, published, or internal.

**Spec sections this task type requires**

- **Behavior held invariant** — what must not change, stated checkably.
- **Call sites** — the inventory, complete.
- **Verification that behavior is unchanged** — the evidence, named.
- **Explicitly out of scope** — the improvements not being made along the way.

Omitting a required section needs its reason written into the spec at that point.

**Red flags**

| Thought | Reality |
|---|---|
| "While I'm in here I'll also fix…" | That is a second change with its own risk. Put it in *Explicitly out of scope*. |
| "Grep found the call sites" | Grep misses dynamic and string-based references. Say how you covered those. |
| "It compiles, so behavior is unchanged" | Compiling is not evidence. Name the check that would catch a behavior change. |
| "No tests cover it, so nothing can break" | That is the riskiest case, not the safest. Decide what evidence replaces the missing tests. |
