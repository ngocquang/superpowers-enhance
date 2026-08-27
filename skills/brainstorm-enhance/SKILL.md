---
name: brainstorm-enhance
description: "Supplement to superpowers:brainstorming — supplies the clarifying-question phase (step 3) as frontier rounds via AskUserQuestion, routed by a task-type playbook that also names the sections the design doc (step 6) must carry. Delivered by the superpowers-enhance hook; invoke manually only to re-read it."
disable-model-invocation: true
---

# Brainstorming

## Scope — two steps, everything else unchanged

This skill touches **two** steps of superpowers:brainstorming.

**Step 3, the clarifying-question phase** ("ask questions one at a time" / "only
one question per message"). For that step the method below *replaces* the base
skill's: ask in rounds, via AskUserQuestion.

**Step 6, the design doc.** A matched playbook names sections that this kind of
task's spec must carry. Those are **added** to the sections the base skill
already asks for. Nothing of the base skill's is replaced or dropped.

Everything else in superpowers:brainstorming is untouched and still mandatory:

- Steps 1–2 (explore project context, offer the visual companion just-in-time)
  run **before** the first round. Playbook matching happens between them and the
  first round.
- Steps 4–9 (propose 2–3 approaches → present design → write the spec doc →
  spec self-review → user reviews the spec → invoke writing-plans) run **after**
  the questioning ends, in that order.
- Classifying the request as spike, bounded or architectural stays the base
  skill's call. A playbook decides content, never ceremony.
- The `<HARD-GATE>` still holds: no code, no scaffolding, no implementation
  skill until the user has approved a design.

## Playbooks

A playbook fixes the *content* of the questioning for one kind of task: which
decision axes the frontier must cover, which facts you go and find instead of
asking, and which sections that task type's spec must carry.

Playbooks live in `playbooks/`, inside this skill's own directory. The injected
wrapper above names that directory's absolute path on a `Skill directory:` line;
if you invoked this skill by hand instead, it is the base directory the harness
announced.

### Match

After step 1 (explore project context) and before the first round, match the
task against this table and say out loud which playbook matched.

| Playbook | Matches when |
|---|---|
| `feature.md` | New or changed behavior in code that already exists |
| `bug-fix.md` | A reported defect to reproduce and root-cause |
| `refactoring.md` | A behavior-preserving change to structure or shape |
| `investigation.md` | A read-only question whose output is an answer, not a change |
| `prototype.md` | A design or empirical fork to settle by building something throwaway |
| `new-project.md` | A new repo, service or subsystem with no existing flow to read |

**Two of them fit?** One is primary — copy that one in. Name the second out loud
and fold its decision axes into the tree with a stated reason. Do not copy two
playbooks in.

**None fit?** Say `no playbook matched`, then run the plain design-tree method
below. Do not stretch the task onto the nearest playbook, and do not invent one.

### Apply

Open the matched file and copy its items into your todo list **verbatim, before
any task-specific todo and before you reason about the task**. The failure this
guards against is reading a playbook, agreeing with it, and then writing your own
plan that quietly drops half of it.

An item you decide not to do stays in the list with `skip: <reason>`. Dropping
one silently is not allowed.

On the bounded and spike paths there is no spec file, so the playbook's
**Spec sections** list is read as a checklist for the short in-chat design.

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
| "I'll just ask this one question first" | That is the base skill's default for step 3; this is the step that runs in rounds. Ask the whole frontier. |
| "I'll ask everything at once to save turns" | Questions downstream of an open question belong to a later round. |
| "Markdown is faster than the tool" | Speed is not the predicate. Enumerable answers → AskUserQuestion. |
| "They might want an answer I didn't list" | The tool already gives them "Other". Use the tool. |
| "Only 4 fit, the rest can wait" | Batch sequential calls. Leftover frontier ≠ next round. |
| "Let me ask the user where that file lives" | Facts are yours. Dispatch a sub-agent. |
| "The sub-agent is still running, I'll wait" | Only the downstream questions wait. Ask the rest now. |
| "Frontier looks empty enough, let's design" | Empty means empty. Name every remaining branch first. |
| "They approved the last round, I can start coding" | The HARD-GATE needs an approved *design*, not answered questions. |
| "I read the playbook, I'll keep it in mind" | Copy its items into the todo list verbatim. Keeping it in mind is the failure mode. |
| "No playbook is a perfect fit, I'll use the closest one" | Say `no playbook matched` and run the plain method. A wrong playbook asks the wrong axes. |
