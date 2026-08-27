### Feature

**When this matches:** new or changed behavior in code that already exists in
this repo. No existing flow to extend means this is not a feature — see
`new-project.md`.

**Decision axes the frontier must cover**

- The user-visible behavior, and its edges: empty, maximum, concurrent, offline.
- Which existing flow this extends, replaces, or sits beside.
- The data shape, and the structure that organizes it — a state machine instead
  of scattered booleans, a table instead of a chain of branches, a typed model
  instead of one shape assumption repeated across files.
- The interface exposed to callers, and who those callers are.
- Failure modes: what breaks, what the user sees, what is recoverable.
- Migration or rollout for data and callers that already exist.
- What is deliberately excluded from this piece of work.

**Facts to dispatch, never ask**

- The call sites of the flow being changed.
- How this repo already does this kind of thing — the pattern to follow.
- Existing test coverage over the surface being touched.

**Spec sections this task type requires**

Added to the base skill's architecture / components / data flow / error handling
/ testing sections:

- **Out of scope** — what was considered and deliberately left out.

Omitting a required section needs its reason written into the spec at that point.

**Red flags**

| Thought | Reality |
|---|---|
| "The data shape is obvious, start from the flow" | Name the shape and its organizing structure first. Every later axis hangs off it. |
| "I'll ask them where the current flow lives" | That is a fact. Dispatch a sub-agent. |
| "Edge cases are an implementation detail" | Edges are behavior. They belong in the frontier, not in code review. |
| "Scope is whatever we don't get to" | Unstated scope becomes the next argument. Write *Out of scope* down. |
