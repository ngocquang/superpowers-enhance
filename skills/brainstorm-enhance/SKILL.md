---
name: brainstorm-enhance
description: "Invoke this whenever the superpowers:brainstorming skill is activated — always invoke both together."
---

# Brainstorming

## Scope — what this replaces, what it does not

This replaces **only** the clarifying-question phase of superpowers:brainstorming
(checklist step 3, "ask questions one at a time" / "only one question per
message"). Where that skill says one question per message, **this skill wins**:
ask in rounds, via AskUserQuestion.

Everything else in superpowers:brainstorming is untouched and still mandatory:

- Steps 1–2 (explore project context, offer the visual companion just-in-time)
  run **before** the first round.
- Steps 4–9 (propose 2–3 approaches → present design → write the spec doc →
  spec self-review → user reviews the spec → invoke writing-plans) run **after**
  the questioning ends, in that order.
- The `<HARD-GATE>` still holds: no code, no scaffolding, no implementation
  skill until the user has approved a design.

## The design tree

Interview the user relentlessly until you reach a shared understanding. Map it
as a **design tree**: every decision branches into the decisions that hang off
it.

## Work the tree in rounds

The **frontier** is every decision whose prerequisites are already settled — the
questions you can ask *now* without guessing at answers you haven't heard yet.

Ask the whole frontier in one round. Then stop and wait for the user's answers
before the next round. Each round of answers reshapes the tree: settled
decisions push the frontier outward and unblock questions that depended on them.
Recompute the frontier and ask the next round.

A question whose answer depends on another question still open in this round
belongs to a *later* round, not this one.

## Ask the round with AskUserQuestion

Put the round to the user with the **AskUserQuestion tool**. That is the default
delivery mechanism for every frontier question.

Your recommended answer is the **first** option of each question, with
`(Recommended)` appended to its label; its description carries the tradeoff.
Never author an "Other" option — the tool adds one, so a question having a
likely-but-not-certain answer is not a reason to skip the tool.

**Frontier larger than the tool's per-call limit?** Split it into batches and
issue the calls **sequentially** — one call, wait for its answers, then the
next, with no other work in between — until the frontier is drained. That is
still **one round**: do not defer leftover frontier questions to a later round.
Only questions *downstream* of an unanswered decision wait.

### Fallback format

Fall back to markdown **only** when a question has no 2–4 enumerable answers —
open-ended narrative ("walk me through your current billing flow", "paste the
error you're seeing"). Then:

```
❓ **Q1** - **<question title>**: <question body, may be multiple paragraphs>

➡️ <your recommended answer>
```

Number those questions and give your recommended answer for each. A round may
mix both: enumerable decisions through the tool, open-ended prompts in markdown.

## Facts are yours; decisions are theirs

Finding *facts* is your job, never the user's. When a frontier question needs a
fact from the environment (filesystem, git history, docs, tools), dispatch a
sub-agent to find it — don't ask the user anything you could look up yourself.

Don't block on it: a running exploration is an unsettled prerequisite, so only
the questions downstream of it wait for the sub-agent to report. Ask the rest of
the frontier now.

The *decisions* are the user's. Put each one to them and wait.

## Done

The questioning is done when the frontier is empty: every branch of the design tree
visited, nothing left silently assumed. Do not act on it until the user confirms
you have reached a shared understanding.

Once they confirm, continue at superpowers:brainstorming step 4 (propose 2–3
approaches) and follow it through to writing-plans.

## Red flags — stop and recompute the frontier

| Thought | Reality |
|---|---|
| "I'll just ask this one question first" | That is brainstorming's rule, not this one. Ask the whole frontier. |
| "I'll ask everything at once to save turns" | Questions downstream of an open question belong to a later round. |
| "Markdown is faster than the tool" | Speed is not the predicate. Enumerable answers → AskUserQuestion. |
| "They might want an answer I didn't list" | The tool already gives them "Other". Use the tool. |
| "Only 4 fit, the rest can wait" | Batch sequential calls. Leftover frontier ≠ next round. |
| "Let me ask the user where that file lives" | Facts are yours. Dispatch a sub-agent. |
| "The sub-agent is still running, I'll wait" | Only the downstream questions wait. Ask the rest now. |
| "Frontier looks empty enough, let's design" | Empty means empty. Name every remaining branch first. |
| "They approved the last round, I can start coding" | The HARD-GATE needs an approved *design*, not answered questions. |
