### New project

**When this matches:** a new repo, service, or subsystem. There is no existing
flow in this codebase to read, which is exactly what makes it not `feature.md`.

**Decision axes the frontier must cover**

- The problem, and who has it today without this.
- Success criteria: what is true when version one is done.
- Decomposition into independent pieces, and the order they get built.
- The stack, and the constraints that pick it — team familiarity, deployment
  target, existing infrastructure.
- Where it runs, who operates it, what happens when it breaks.
- What version one deliberately does not do.

**Facts to dispatch, never ask**

- Conventions in the surrounding org or sibling repos — layout, CI, naming.
- Whether something already exists that solves part of this.

**Spec sections this task type requires**

Added to the base skill's architecture / components / data flow / error handling
/ testing sections:

- **Decomposition and build order** — the independent pieces and their sequence.
- **Deliberately deferred** — what is out of version one, and why.

The base skill's own rule applies first: a project spanning several independent
subsystems gets decomposed before any of it gets specified, and each piece then
runs its own spec → plan → implementation cycle. Omitting a required section
needs its reason written into the spec at that point.

**Red flags**

| Thought | Reality |
|---|---|
| "Let me refine the details of all four subsystems" | Decompose first. Detail on a project that needs splitting is wasted. |
| "The stack is whatever I know best" | Name the constraints that pick it. That is a decision the user owns. |
| "Version one should be complete" | *Deliberately deferred* is a section, not an oversight. Fill it in. |
| "Operations can come later" | Where it runs shapes the architecture. It is a frontier axis, not a follow-up. |
