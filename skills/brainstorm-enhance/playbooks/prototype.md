### Prototype

**When this matches:** a design or empirical fork you can settle by building
something throwaway and looking at it — which layout, which interaction, which
timing, which approach. Reach for this instead of asking the user a question an
experiment could answer.

**Decision axes the frontier must cover**

- The single decision this prototype exists to settle. No decision, no prototype.
- Which variants are worth building, and what makes them meaningfully different.
- What observation decides between them — the eye, a timing, an output.
- What "enough" looks like, so the sketch stops.
- Where the throwaway lives, kept out of production source.

**Facts to dispatch, never ask**

- Prior art for this interaction, in this repo and outside it.
- The lightest stack that renders the question honestly.

**Spec sections this task type requires**

- **Decision being settled** — one sentence.
- **Variants** — what each one is trying.
- **How the observation decides** — named before building, not after.
- **Throwaway location** — and a plain statement that the code is throwaway.

Omitting a required section needs its reason stated with it.

**Red flags**

| Thought | Reality |
|---|---|
| "I'll ask which layout they prefer" | Build both and show them. The ask is the slow path. |
| "This came out well, let's keep the code" | Keeping it is a new request. Re-enter brainstorming as `feature.md`. |
| "Add tests and clean it up first" | Code quality does not matter here. The rigor is in choosing the decision and the observation. |
| "One variant is enough to see" | One variant has nothing to lose to. Build the alternative you expect to reject. |
