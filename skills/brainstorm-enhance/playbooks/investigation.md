### Investigation

**When this matches:** a read-only question. "How does X work", "why was Y built
this way", "are we sure about Z", "should we do X or Y". The output is an
answer, not a change.

The frontier here is small on purpose. Almost everything is a fact, and facts
are yours.

**Decision axes the frontier must cover**

- What decision the answer feeds, and who makes it.
- What evidence would actually settle it.
- The confidence bar: a quick read, or something you would bet a release on.
- Whether they want a recommendation or only the findings.

**Facts to dispatch, never ask**

- Nearly everything. Code paths, git history, docs, issue history, runtime
  behavior. If it can be observed by running or reading something, dispatch it.

**Spec sections this task type requires**

- **Question** — restated precisely.
- **Evidence** — with citations to the files, commits, or runs it came from.
- **Answer** — including your real judgment when the question asks for one.
- **Confidence, and what would change it.**

On the spike path this replaces a spec file entirely: the report *is* the
deliverable. Omitting a required section needs its reason stated with it.

**Red flags**

| Thought | Reality |
|---|---|
| "Let me ask them how the system works" | That is the question they asked you. Go read it. |
| "I'll list both sides and let them decide" | If they asked "should we", give your judgment with reasons. |
| "Plausible enough to state as fact" | Cite it or mark it uncertain. An uncited claim is a guess in a confident voice. |
| "The investigation found a bug, I'll just fix it" | Report it and re-enter brainstorming as `bug-fix.md`. This playbook ships no code. |
